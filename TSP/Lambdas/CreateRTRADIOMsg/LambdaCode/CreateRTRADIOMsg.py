import json
import logging
import os

import boto3
import redis
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session

client = boto3.client("iot-data", os.environ["AWS_REGION"])
base_url = os.environ["CDF_URL"]

REDIS_URL = os.environ["REDIS_URL"]
REDIS_PORT = os.environ["REDIS_PORT"]

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

# ToDo: Use desribe_cache_clusters() to get the URL dynamically rather than have a static URL loaded from Assets/Env
# Create the connection to the Redis Elasticache cluster
cache = redis.Redis(host=REDIS_URL, port=REDIS_PORT, db=0, decode_responses=True)


# Log Levels listed with the top level being the most verbose
# and the bottom being the least verbose:
# DEBUG
# INFO
# WARN
# ERROR
# FATAL
logging.basicConfig(level=logging.INFO)


# default
# MP70 does not provide RSSI information set to 0
vehicle_rssi = b"\x00\x00"
# filler
padding = b"\x00\x00"
# CMS can go to CDF to get this info directly
satellite_gps = b"\x00\x00\x00\x00"
# always 0
conditional_priority = b"\x00"
# modem has no slot
veh_diag_value = b"\x00\x00\x00\x00"
# possible gpi values with turn signal on
GPI_WITH_TURN_SIGNAL = [3, 5, 11, 13, 19, 21, 27, 29]
GPI_WITHOUT_TURN_SIGNAL = [1, 9, 17, 25]

# seconds for which gpi value in cache is valid
VALID_CACHE_GPI = 4


def convert_lat_lon_to_minutes_degrees(lat, lon):
    return_lat = to_min_degrees(lat)
    return_lon = to_min_degrees(lon)
    return return_lat, return_lon


def to_min_degrees(data):
    data = float(data)
    ddd = int(data)
    mmmmmm = float(data - float(ddd)) * 60
    data = (ddd * 1000000 + int(mmmmmm * 10000)) / 1000000
    new_string = hex(int(data * 1000000))
    int_data = int(new_string, 16)
    return_data = int_data.to_bytes(4, byteorder="little", signed=True)
    return return_data


# message sent from device is in kilometers/hour scaled down by 5
def convert_speed(speed):
    new_speed = int(speed * 1000 * 5 / 3600)
    return new_speed.to_bytes(1, byteorder="little", signed=False)


def convert_heading(heading):
    new_heading = int(heading / 2 + 0.5)
    return new_heading.to_bytes(1, byteorder="little", signed=False)


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )  # noqa: E501
    return URLLib3Session().send(request.prepare()).content


def lambda_handler(event, context):
    pub_topic = event.get("topic")
    if not pub_topic:
        raise Exception("No topic in event data")

    logging.info(f"Topic message received from:{pub_topic}, event: {event}")

    # get SN from topic
    # Topic is always 'SW/+/GTT/SIERRA/VEH/TSP/MP70/' where '+' denotes the serial number of the modem
    split_topic = pub_topic.split("/")
    client_id = split_topic[1]
    logging.info(f"Client ID: {client_id}")
    redis_key = f"cdf_cache:{client_id.lower()}"

    # get data from the cache
    cache_data = cache.hgetall(name=redis_key)
    if cache_data:
        logging.debug(f"Data from cache: {cache_data}")
    else:
        logging.debug("Data not found in cache. Trying to get data from CDF.")
    # Epoch time is used for the key
    time = list(event.keys())[0]
    gps_data = event.get(time)
    if cache_data.get("ID"):
        logging.info("Cache data found. Publishing RTRADIO Message.")
        create_topic_and_publish(
            time,
            event.get(time),
            cache_data["vehicleID"],
            cache_data["vehicleClass"],
            cache_data["vehicleCityID"],
            cache_data["agencyID"],
            cache_data["vehicleSerialNo"],
            cache_data["CMSID"],
            cache_data["ID"],
            cache_data["GTTSerial"],
            cache_data["vehicleMode"],
            cache_data["GPIO"],
            cache_data["GPIOTimeStamp"],
        )
    else:
        # Assemble URL for communicator
        url = f"{base_url}/devices/{client_id.lower()}"
        logging.debug(f"CDF URL being hit: {url}")
        code = send_request(url, "GET", os.environ["AWS_REGION"], headers=headers)

        communicator_data = json.loads(code)
        logging.debug(f"Response from CDF - Communicator Data: {communicator_data}")
        # check to see if communicator
        template_id = communicator_data.get("templateId")
        if not template_id:
            raise Exception(
                f"Serial No. is {client_id} No template id in device CDF data"
            )

        # Only work with SCP vehicle modems
        if template_id == "communicator":
            # get region and agency name from device CDF data
            groups = communicator_data.get("groups")

            if groups:
                out = groups.get("out")
            else:
                raise Exception(
                    f"Serial No. is {client_id} No groups in communicator CDF data"
                )

            # sometimes device data has out sometimes it doesn't; handle both cases
            if out:
                ownedby = out.get("ownedby")
            else:
                ownedby = groups.get("ownedby")

            agency = ownedby[0].split("/")[2]
            region = ownedby[0].split("/")[1]

            # get attributes from communicator CDF data
            communicator_attributes = communicator_data.get("attributes")
            if not communicator_attributes:
                raise Exception(
                    f"Serial No. is {client_id} No attributes value in communicator CDF data"
                )

            gtt_serial = communicator_attributes.get("gttSerial")
            if not gtt_serial:
                raise Exception(
                    f"Serial No. is {client_id} No gtt_serial value in attributes"
                )

            mac_address = communicator_attributes.get("addressMAC")
            if not mac_address:
                raise Exception(
                    f"Serial No. is {client_id} No MAC address value in attributes"
                )

            # use communicator data to get vehicle data
            devices = communicator_data.get("devices")

            if devices:
                devices_in = devices.get("in")
            if not devices:
                raise Exception(
                    f"Serial No. is {client_id} No associated vehicle in communicator CDF data"
                )

            # sometimes device data has out sometimes it doesn't; handle both cases
            if devices_in:
                installedat = devices_in.get("installedat")
            else:
                installedat = devices.get("installedat")

            vehicle = installedat[0]

            # Assemble URL for vehicle
            url = f"{base_url}/devices/{vehicle.lower()}"

            code = send_request(
                url, "GET", os.environ["AWS_REGION"], headers=headers
            )  # noqa: E501

            vehicle_data = json.loads(code)
            vehicle_attributes = vehicle_data.get("attributes")
            if not vehicle_attributes:
                raise Exception(
                    f"Serial No. is {client_id} No attributes value in vehicle CDF data"
                )

            # use communicator data to get agency data
            url = f"{base_url}/groups/%2F{region}%2F{agency}"

            code = send_request(
                url, "GET", os.environ["AWS_REGION"], headers=headers
            )  # noqa: E501

            agency_data = json.loads(code)
            agency_attributes = agency_data.get("attributes")
            if not agency_attributes:
                raise Exception(
                    f"Serial No. is {client_id} No attributes value in Agency json string"
                )

            agency_code = agency_attributes.get("agencyCode")
            if not agency_code:
                raise Exception(
                    f"Serial No. is {client_id} Agency Code not found in CDF"
                )

            agency_id = agency_attributes.get("agencyID")
            cms_id = agency_attributes.get("CMSId")
            if not agency_id:
                raise Exception(
                    f"Serial No. is {client_id} Agency ID (GUID) not found in CDF"
                )

            if not cms_id:
                raise Exception(
                    f"Serial No. is {client_id} Agency Id is {agency_id} CMS ID (GUID) not found in CDF"
                )

            mac_address = mac_address.replace(":", "")[-6:]
            try:
                unit_id_binary = bin(int(mac_address, 16))[2:].zfill(24)

                # unit_id = 0x800000 | mac_address
                orrer = f"{8388608:024b}"
                orred_unit_id = ""

                for i in range(0, 24):
                    orred_unit_id += str(int(orrer[i]) | int(unit_id_binary[i]))

                unit_id = int(orred_unit_id, 2)
            except Exception as e:
                raise Exception(
                    f"Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id} MAC address is not numeric : {e}"
                )

            vehicle_id = vehicle_attributes.get("VID")
            # get agency id from CDF but default to 1
            vehicle_city_id = agency_code

            # veh mode
            priority = vehicle_attributes.get("priority")
            if priority == "High":
                vehicle_mode = 0
            else:
                vehicle_mode = 1

            # get Class from CDF
            vehicle_class = vehicle_attributes.get("class")
            if not vehicle_class:
                raise Exception(
                    f"Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id} No class in device attributes"
                )

            # set gpio to current gpio value and make it a int for comparison later
            gpio = int(gps_data.get("atp.gpi"))

            create_topic_and_publish(
                time,
                gps_data,
                vehicle_id,
                vehicle_class,
                vehicle_city_id,
                agency_id,
                unit_id,
                cms_id,
                client_id.lower(),
                gtt_serial,
                vehicle_mode,
                gpio,
                time,
            )
            insert_in_cache(
                client_id.lower(),
                vehicle_id,
                vehicle_class,
                vehicle_city_id,
                agency_id,
                gtt_serial,
                cms_id,
                unit_id,
                vehicle_mode,
                gpio,
                time,
            )
        else:
            logging.error(
                f"Serial No. is {client_id} communicator does not have templateId; exiting "
            )
            raise Exception(
                f"Serial No. is {client_id} communicator does not have templateId; exiting "
            )


def create_topic_and_publish(
    message_time,
    gps_data,
    vehicle_id,
    vehicle_class,
    vehicle_city_id,
    agency_id,
    unit_id,
    cms_id,
    client_id,
    gtt_serial,
    vehicle_mode,
    gpio,
    gpio_timestamp,
):
    # assuming agency code is always available as it is required field in CDF templates
    vehicle_city_id_bytes = int(vehicle_city_id).to_bytes(
        1, byteorder="little", signed=False
    )
    # assuming vehicle class is always available as it is required field in CDF templates
    vehicle_class_bytes = int(vehicle_class).to_bytes(
        1, byteorder="little", signed=False
    )

    # assuming vehicle id is always available as it is required field in CDF templates
    vehicle_id_bytes = int(vehicle_id).to_bytes(2, byteorder="little", signed=False)
    # assuming Mac address(used to generate unit_id) is always available in CDF as it is required field for MP-70
    unit_id_bytes = int(unit_id).to_bytes(4, byteorder="little", signed=False)

    # parse new data from incoming GPS message
    lat = gps_data.get("atp.glat")  # Current latitude
    lon = gps_data.get("atp.glon")  # Current longitude
    hdg = gps_data.get("atp.ghed")  # Current heading
    spd = gps_data.get("atp.gspd")  # Current speed kmph
    stt = gps_data.get("atp.gstt")  # GPS fix status (0 = no fix, 1 = fix)
    live_gpi = gps_data.get("atp.gpi")  # GPIO state - bit masked

    # process GPS message and create RTRADIO message
    # incoming latitude needs to be converted to degrees/minutes because
    # CMS expects it in that format

    # Raising an Exception if the lat lon values are out of range. Logging the same values as well.
    if (-90 <= lat <= 90) and (-180 <= lon <= 180):
        gps_lat_dddmmmmmm, gps_lon_dddmmmmmm = convert_lat_lon_to_minutes_degrees(
            lat, lon
        )
    else:
        raise Exception(
            f"Serial No. is {client_id} Lat: {lat} Lon: {lon} are not in the valid range"
        )

    _latitude_100 = lat * 100
    _latitude_100_whole = int(_latitude_100)
    round_latitude = "L"
    remainder = abs(_latitude_100) - abs(_latitude_100_whole)
    if remainder >= 0.5:
        round_latitude = "H"
    _latitude_2_decimal = _latitude_100_whole / 100
    _latitude_2_decimal_str = (
        f"{_latitude_2_decimal:0.2f}"  # Casting it to be strictly 2 decimals
    )

    _longitude_100 = lon * 100
    _longitude_100_whole = int(_longitude_100)
    round_longitude = "L"
    remainder = abs(_longitude_100) - abs(_longitude_100_whole)
    if remainder >= 0.5:
        round_longitude = "H"
    _longitude_2_decimal = _longitude_100_whole / 100
    _longitude_2_decimal_str = (
        f"{_longitude_2_decimal:0.2f}"  # Casting it to be strictly 2 decimals
    )

    # IO Mapping
    # IO 1 == ignition
    # IO 2 == left blinker
    # IO 3 == right blinker
    # IO 4 == light bar
    # IO 5 == disable

    gpio = int(gpio)
    # use cached value of gpio if a high value of gpi is retrieved from cache having timestamp within last x seconds
    # use absolute difference to take care of out of order messages received(older message received at later point) in IoT core
    if (
        live_gpi in GPI_WITHOUT_TURN_SIGNAL
        and gpio in GPI_WITH_TURN_SIGNAL
        and abs(int(message_time) - int(gpio_timestamp)) <= VALID_CACHE_GPI
    ):
        calculated_gpi = int(gpio)
    else:
        calculated_gpi = live_gpi

    # use GPIO information
    ignition = calculated_gpi & 0x01
    left_turn = (calculated_gpi & 0x02) >> 1
    right_turn = (calculated_gpi & 0x04) >> 1  # shift only one for math below
    light_bar = (calculated_gpi & 0x08) >> 3
    disable = (calculated_gpi & 0x10) >> 4

    # turn status
    turn_status = left_turn
    turn_status |= right_turn

    # op status
    op_status = 0
    if not ignition or disable:
        op_status = 0
    elif light_bar and ignition and not disable:
        op_status = 1

    # pack up data
    veh_mode_op_turn = turn_status
    veh_mode_op_turn |= op_status << 2
    veh_mode_op_turn |= int(vehicle_mode) << 5
    veh_mode_op_turn = veh_mode_op_turn.to_bytes(1, byteorder="little", signed=False)

    # gspd is km/h coming from the MP70, needs to be converted to
    # (meters / 5)/second
    velocity_mpsd5 = convert_speed(spd)

    # ghed is heading in degrees coming from the MP70, needs to be converted
    # to heading per two degrees
    hdg_deg2 = convert_heading(hdg)

    # gstt is only 0 or 1, so we don't have 3D or 3D+ as possibilities
    gps_status = 0
    if stt == 0:
        gps_status &= 0x3FFF
    else:
        gps_status |= 0xC000

    gpsc_stat = gps_status.to_bytes(2, byteorder="little", signed=False)

    # assemble message
    message_data = (
        unit_id_bytes
        + vehicle_rssi
        + padding
        + gps_lat_dddmmmmmm
        + gps_lon_dddmmmmmm
        + velocity_mpsd5
        + hdg_deg2
        + gpsc_stat
        + satellite_gps
        + vehicle_id_bytes
        + vehicle_city_id_bytes
        + veh_mode_op_turn
        + vehicle_class_bytes
        + conditional_priority
        + padding
        + veh_diag_value
    )

    # out going topic structure "GTT/GTT/VEH/EVP/2101/2101ET0001/RTRADIO"
    # where second GTT is replaced with the CMS ID
    new_topic = f"GTT/{cms_id.lower()}/VEH/EVP/2101/{gtt_serial}/RTRADIO"
    # replace VEH with SVR
    new_topic = new_topic.replace("VEH", "SVR", 1)
    new_topic += (
        "/"
        + _latitude_2_decimal_str
        + round_latitude
        + ","
        + _longitude_2_decimal_str
        + round_longitude
    )
    logging.info(f"Message: {message_data} to Topic: {new_topic} is being sent")
    # Send out new Topic to CMS associated with the client_id
    response = client.publish(topic=new_topic, qos=0, payload=message_data)
    logging.info(
        f"GTT Serial No. is {gtt_serial}, Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id} {response}"  # noqa: E501
    )

    # update the cache if current gpio is in [3,5,11,13,19,21,27,29]||GPI_WITH_TURN_SIGNAL
    # and time and gpio time not equal, because if they are equal, it is creation not update in cache
    # message_time > gpio_timestamp takes care of case if older message is received at a later point
    if live_gpi in GPI_WITH_TURN_SIGNAL and int(message_time) > int(gpio_timestamp):
        redis_key = f"cdf_cache:{client_id}"
        try:
            responseGPIO = cache.hset(name=redis_key, key="GPIO", value=live_gpi)
            responseGPIOTimeStamp = cache.hset(
                name=redis_key, key="GPIOTimeStamp", value=message_time
            )
            logging.info(
                f"GPIO and GPIOTimeStamp inserted to Redis: {responseGPIO, responseGPIOTimeStamp}"
            )
        except Exception as RedisUpdateException:
            logging.exception(f"Update to Redis failed. Error: {RedisUpdateException}")


def insert_in_cache(
    client_id,
    vehicle_id,
    vehicle_class,
    vehicle_city_id,
    agency_id,
    gtt_serial,
    cms_id,
    unit_id,
    vehicle_mode,
    gpio,
    gpio_timestamp,
):
    item = {
        "ID": client_id,
        "vehicleID": vehicle_id,
        "vehicleClass": vehicle_class,
        "vehicleCityID": vehicle_city_id,
        "agencyID": agency_id,
        "GTTSerial": gtt_serial,
        "CMSID": cms_id,
        "vehicleSerialNo": unit_id,
        "vehicleMode": vehicle_mode,
        "GPIO": gpio,
        "GPIOTimeStamp": gpio_timestamp,
    }

    redis_key = f"cdf_cache:{client_id}"
    try:
        updatedRows = cache.hset(name=redis_key, mapping=item)
        logging.info(f"{updatedRows} number of rows written to Redis succesfully.")
    except Exception as RedisSetException:
        logging.error(f"Could not write item to Redis. Error: {RedisSetException}")
        raise Exception(RedisSetException)

    if not cache.expire(name=redis_key, time=1200):
        logging.error("Could not set expiry on Redis item.")
        raise Exception("Could not set expiry on Redis item.")
