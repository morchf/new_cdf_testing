import json
from boto3 import client
from boto3 import Session
from os import environ
from time import time
from base64 import b64decode
from struct import pack
from struct import unpack
from math import trunc
from redis import Redis

from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth

ioTclient = client("iot-data", environ["AWS_REGION"])
base_url = environ["CDF_URL"]

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

start_time = None


def connectToRedis():
    # These two parameters below needs to be set in the environment variable.
    redis_address = environ["RedisEndpointAddress"]  # redis_cache
    redis_port = environ["RedisEndpointPort"]
    # the parameter -> "utf-8" allows to convert to Unicode, since Redis returns binary Data.
    cache = Redis(
        host=redis_address,
        port=redis_port,
        db=0,
        charset="utf-8",
        decode_responses=True,
    )  # redis_cache
    return cache


# default
# MP70 does not provide RSSI information set to 0
vehicle_rssi = b"\x00\x00"
# filler
padding = b"\x00\x00"
gps_status = 0
# CMS can go to CDF to get this info directly
satellite_gps = b"\x00\x00\x00\x00"
op_status = 0
# always 0
conditional_priority = b"\x00"
# modem has no slot
veh_diag_value = b"\x00\x00\x00\x00"
gpsStatus = 35716


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


def rawbytes(s):
    """Convert a string to raw bytes without encoding"""
    outlist = []
    for cp in s:
        num = ord(cp)
        if num < 255:
            outlist.append(pack("B", num))
        elif num < 65535:
            outlist.append(pack(">H", num))
        else:
            b = (num & 0xFF0000) >> 16
            H = num & 0xFFFF
            outlist.append(pack(">bH", b, H))
    return b"".join(outlist)


# message sent from device is in kilometers/hour scaled down by 5
def convert_speed(speed):
    speed = int(speed)
    new_speed = int(speed * 1000 * 5 / 3600)
    return new_speed.to_bytes(1, byteorder="little", signed=False)


def convert_heading(heading):
    heading = int(heading)
    new_heading = int(heading / 2 + 0.5)
    return new_heading.to_bytes(1, byteorder="little", signed=False)


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )  # noqa: E501
    return URLLib3Session().send(request.prepare()).content


def post_log(whelen_data, iot_timestamp, serial, device_timestamp):
    """log action - push log to S3 Via Kinesis Firehose
    Args:
        whelen_data in json,
        (Data format:
            dateTime, device_timestamp,
            disable, enable,
            gps: struct<direction,latitude,longitude,speed>,
            iot_timestamp, messageId, topic, turnSignal
        )
        iot_timestamp,
        serial,
        device_timestamp
    """

    firehoseClient = client("firehose", region_name="us-east-1")
    streamname = (
        "whelen_delivery_stream"  # This stream needs to be created in Kinesis FIREHOSE!
    )

    try:
        # Append topic and timestamps to raw whelen data.
        whelen_data["topic"] = serial
        whelen_data["iot_timestamp"] = iot_timestamp
        whelen_data["device_timestamp"] = device_timestamp

        # logging.info(f"Log Data - {whelen_data}")
        # log_data.append({"Data": (json.dumps(log) + ",").encode()})
        result = firehoseClient.put_record(
            DeliveryStreamName=streamname,
            Record={"Data": (json.dumps(whelen_data) + ",")}
            # Note: json.dumps() converts it into a string. A comma is concatenated as a basic pre-processing step to differentiate
            # multiple records when it lands into S3 bucket in a text-like format.
        )
        result = f"Log Result = {result}"
        # print("Firehose result: ", result)
        # logging.info(result)
        return result
    except Exception as e:
        result = f"Error - {e}"
        print(
            "post_log Error - {e} - {whelen_data}, {iot_timestamp}, {serial}, {device_timestamp}"
        )
        # logging.error(result)
        return result


def lambda_handler(event, context):
    # if the lambda is called via
    if not event.get("messages"):
        # print(f"No Messages found - event = {event}")
        return
    cache = connectToRedis()
    for message in event["messages"]:
        data = message["data"]
        # print(f"event = {event}")
        bytes = rawbytes(data)
        dataDecode = str(b64decode(bytes))
        # (f"dataDecode = {dataDecode}")

        dataDecode = dataDecode[2 : len(dataDecode) - 1]
        # print(f"dataDecode decode = {dataDecode}")

        data = json.loads(str(dataDecode))

        destination = message["destination"]["physicalName"]
        # print(f"destination = {destination}")
        # get SN from topic
        # Topic is always SN/messages/json where SN is the serial number of the modem
        split_topic = destination.split(".")
        client_id = split_topic[1]
        # print(f"client_id = {client_id.lower()}")
        # print(f"client_id_type = {tyype}")
        # get data from the cache
        # cache_data = cache.get_item(Key={"ID": client_id.lower()})
        cache_data = cache.hgetall(client_id.lower())  # redis_cache

        # print("Cache data: ", cache_data)

        # Epoch time is used for the key
        # time = message["timestamp"]
        gps_data = data

        if cache_data:  # redis_cache
            compile_2100_msg(
                gps_data,
                cache_data["vehicleID"],
                cache_data["vehicleClass"],
                cache_data["vehicleCityID"],
                cache_data["agencyID"],
                cache_data["vehicleSerialNo"],
                cache_data["CMSID"],
                cache_data["ID"],
                cache_data["GTTSerial"],
                cache_data["vehicleMode"],
                start_time,
            )
        else:
            # Assemble URL for communicator
            url = f"{base_url}/devices/{client_id.lower()}"
            # print(f"url = {url}")
            communicator_data = ""
            try:
                code = send_request(url, "GET", environ["AWS_REGION"], headers=headers)
                # print(f"code = {code}")
                communicator_data = json.loads(code)
            except Exception as e:
                print(f"[ERROR] send_request FAIL {e} - {event}")
                return
            # print(f"communicator_data = {communicator_data}")
            # check to see if communicator
            template_id = str(communicator_data.get("templateId", "NONE"))
            if not template_id:
                print(f"[ERROR]No template id in device CDF data - {event}")
                return

            template_id = template_id
            print(f"template_id = {template_id}")
            # Only work with SCP vehicle modems
            if template_id == "whelencom":
                # get region and agency name from device CDF data
                groups = communicator_data.get("groups")

                if groups:
                    out = groups.get("out")
                else:
                    print(f"[ERROR]No groups in communicator CDF data - {event}")
                    return

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
                    print(
                        f"[ERROR]No attributes value in communicator CDF data - {event}"
                    )
                    return

                gtt_serial = communicator_attributes.get("gttSerial")
                if not gtt_serial:
                    print(f"[ERROR]No gtt_serial value in attributes - {event}")
                    return

                mac_address = communicator_attributes.get("addressMAC")
                if not mac_address:
                    print(f"[ERROR]No MAC address value in attributes - {event}")
                    return
                # use communicator data to get vehicle data
                devices = communicator_data.get("devices")

                if devices:
                    devices_in = devices.get("in")
                if not devices:
                    print(
                        f"[ERROR]No associated vehicle in communicator CDF data - {event}"
                    )
                    return
                # sometimes device data has out sometimes it doesn't; handle both cases
                if devices_in:
                    installedat = devices_in.get("installedat")
                else:
                    installedat = devices.get("installedat")

                vehicle = installedat[0]

                # Assemble URL for vehicle
                url = f"{base_url}/devices/{vehicle.lower()}"

                code = send_request(
                    url, "GET", environ["AWS_REGION"], headers=headers
                )  # noqa: E501

                vehicle_data = json.loads(code)
                vehicle_attributes = vehicle_data.get("attributes")
                if not vehicle_attributes:
                    print(f"[ERROR]No attributes value in vehicle CDF data - {event}")
                    return
                # use communicator data to get agency data
                url = f"{base_url}/groups/%2F{region}%2F{agency}"

                code = send_request(
                    url, "GET", environ["AWS_REGION"], headers=headers
                )  # noqa: E501

                agency_data = json.loads(code)
                agency_attributes = agency_data.get("attributes")
                if not agency_attributes:
                    print(f"[ERROR]No attributes value in Agency json string - {event}")
                    return
                agency_code = agency_attributes.get("agencyCode")
                if not agency_code:
                    print(f"[ERROR]Agency Code not found in CDF - {event}")
                    return
                agency_id = agency_attributes.get("agencyID")
                cms_id = agency_attributes.get("CMSId")
                if not agency_id:
                    print(f"[ERROR]Agency ID (GUID) not found in CDF - {event}")
                    return
                if not cms_id:
                    print(f"[ERROR]CMS ID (GUID) not found in CDF - {event}")
                    return
                mac_address = mac_address.replace(":", "")[-6:]
                try:
                    unit_id_binary = bin(int(mac_address, 16))[2:].zfill(24)

                    # unit_id = 0x800000 | mac_address
                    orrer = f"{8388608:024b}"
                    orred_unit_id = ""

                    for i in range(0, 24):
                        orred_unit_id += str(int(orrer[i]) | int(unit_id_binary[i]))

                    unit_id = int(orred_unit_id, 2)
                except:
                    print(f"[ERROR]MAC address is not numeric - {event}")
                    return
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
                    print(f"[ERROR]No class in device attributes - {event}")
                    return
                compile_2100_msg(
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
                    start_time,
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
                    cache,
                )
            else:
                print(
                    f"[ERROR]communicator does not have templateId; exiting - {event}"
                )
                return

        # Log sent to Firehose at the end of the execution to maximize lambda's performance.
        post_log(data, message["brokerInTime"], client_id, message["timestamp"])


def compile_2100_msg(
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
    start_time,
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
    if gps_data.get("gps", None) is not None:
        lat = gps_data.get("gps").get("latitude")  # Current latitude
        lon = gps_data.get("gps").get("longitude")  # Current longitude
        hdg = gps_data.get("gps").get("direction")  # Current heading
        spd = gps_data.get("gps").get("speed")  # Current speed kmph

    else:
        lat = gps_data.get("latitude")  # Current latitude
        lon = gps_data.get("longitude")  # Current longitude
        hdg = gps_data.get("direction")  # Current heading
        spd = gps_data.get("speed")  # Current speed kmph

    stt = 1  # GPS fix status (0 = no fix, 1 = fix)
    gpi = 0  # GPIO state - bit masked

    gps_en = gps_data.get("enable", None)
    # print(f"gps_en = {gps_en}")

    # process GPS message and create RTRADIO message
    # incoming latitude needs to be converted to degrees/minutes because
    # CMS expects it in that format
    gps_lat_dddmmmmmm, gps_lon_dddmmmmmm = convert_lat_lon_to_minutes_degrees(lat, lon)

    # IO Mapping
    # IO 1 == ignition
    # IO 2 == left blinker
    # IO 3 == right blinker
    # IO 4 == light bar
    # IO 5 == disable
    # use new GPIO data if available
    gpi = 0

    # use GPIO information
    ignition = 1
    left_turn = 0  # (gpi & 0x02) >> 1
    right_turn = 0  # (gpi & 0x04) >> 1  # shift only one for math below
    light_bar = (gpi & 0x08) >> 3
    disable = 0

    turnSignal = gps_data.get("turnSignal")
    if turnSignal == "left":
        left_turn = 1

    if turnSignal == "right":
        right_turn = 1

    # turn status
    turn_status = left_turn
    turn_status |= right_turn

    # op status

    op_status = 1
    if not ignition or disable:
        op_status = 0
    elif light_bar and ignition and not disable:
        op_status = 1

    try:
        if not gps_en:
            op_status = 0
    except Exception as e:
        print(f"[ERROR] - {e}")

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
    global gps_status
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
    # print(
    #     f"message data = {unit_id_bytes} {vehicle_rssi} {padding} {gps_lat_dddmmmmmm} {gps_lon_dddmmmmmm} {velocity_mpsd5} {hdg_deg2} {gpsc_stat} {satellite_gps} {vehicle_id_bytes} {vehicle_city_id_bytes} {veh_mode_op_turn} {vehicle_class_bytes} {conditional_priority} {padding} {veh_diag_value}"
    # )
    # out going topic structure "GTT/GTT/VEH/EVP/2100/2100ET0001/RTRADIO"
    # where second GTT is replaced with the CMS ID
    new_topic = f"GTT/{cms_id.lower()}/VEH/EVP/2100/{gtt_serial}/RTRADIO"
    # old_topic = new_topic

    # Send out new Topic to CMS associated with the client_id
    # response = client.publish(topic=new_topic, qos=0, payload=message_data)
    try:
        new_topic = get_2100_topic(message_data, new_topic, cms_id)
        ioTclient.publish(topic=new_topic, qos=0, payload=message_data)
        # print(
        #     f"GTT Serial No. is {gtt_serial}, Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id}"  # noqa: E501
        # )
    except Exception as e:
        print(f"[ERROR] Publication FAIL {e}")


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
    cache,
):
    current_time = int(time())
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
        "ExpirationTime": current_time + 1200,
    }
    # cache.put_item(Item=item)

    cache.hmset(client_id, item)  # redis_cache


def get_2100_topic(
    message,
    pub_topic,
    cms_id,
):

    latitude = message[8:12]
    _latitude = unpack("<i", latitude)[0]

    MINLATITUDE = -90
    MAXLATITUDE = 90

    _dec = _latitude * 0.000001
    _dec_int = trunc(_dec)
    # Minutes shift over two decimal places and divide by 60
    MMmm = (abs(_dec) - abs(_dec_int)) * 100

    if _dec_int > 0:
        _latitude = _dec_int + MMmm / 60
    elif _dec_int < 0:
        _latitude = _dec_int - MMmm / 60
    elif _dec_int == 0:
        if _dec < 0:
            _latitude = -MMmm / 60
        else:
            _latitude = MMmm / 60

    if _latitude > MAXLATITUDE:
        _latitude = MAXLATITUDE
    elif _latitude < MINLATITUDE:
        _latitude = MINLATITUDE

    _latitude_100 = _latitude * 100
    _latitude_100_whole = int(_latitude_100)
    _latitude_2_decimal = _latitude_100_whole / 100
    _latitude_2_decimal_str = f"{_latitude_2_decimal:0.2f}"

    _lat_dec_count = len(_latitude_2_decimal_str.split(".")[1])

    if _latitude_2_decimal == 0 or _lat_dec_count < 2:  # for case when latitude is 0
        _latitude_2_decimal_str = format(_latitude_2_decimal, ".2f")

    round_latitude = "L"
    remainder = abs(_latitude_100) - abs(_latitude_100_whole)
    if remainder >= 0.5:
        round_latitude = "H"

    longitude = message[12:16]
    _longitude = unpack("<i", longitude)[0]

    MINLONGITUDE = -180
    MAXLONGITUDE = 180

    _dec = _longitude * 0.000001
    _dec_int = trunc(_dec)
    # Minutes shift over two decimal places and divide by 60
    MMmm = (abs(_dec) - abs(_dec_int)) * 100

    if _dec_int > 0:
        _longitude = _dec_int + MMmm / 60
    elif _dec_int < 0:
        _longitude = _dec_int - MMmm / 60
    elif _dec_int == 0:
        if _dec < 0:
            _longitude = -MMmm / 60
        else:
            _longitude = MMmm / 60

    if _longitude > MAXLONGITUDE:
        _longitude = MAXLONGITUDE
    elif _longitude < MINLONGITUDE:
        _longitude = MINLONGITUDE

    _longitude_100 = _longitude * 100
    _longitude_100_whole = int(_longitude_100)
    _longitude_2_decimal = _longitude_100_whole / 100
    _longitude_2_decimal_str = f"{_longitude_2_decimal:0.2f}"

    _long_dec_count = len(_longitude_2_decimal_str.split(".")[1])

    if _longitude_2_decimal == 0 or _long_dec_count < 2:  # for case when longitude is 0
        _longitude_2_decimal_str = format(_longitude_2_decimal, ".2f")

    round_longitude = "L"
    remainder = abs(_longitude_100) - abs(_longitude_100_whole)
    if remainder >= 0.5:
        round_longitude = "H"

    # replace VEH with SVR
    pub_topic = pub_topic.replace("VEH", "SVR", 1)
    # Create new Topic to send to specific CMS
    new_topic = pub_topic[:4] + pub_topic[4:].replace(
        "GTT", cms_id.lower()
    )  # replaces second GTT in string with cms_id
    new_topic += (
        "/"
        + _latitude_2_decimal_str
        + round_latitude
        + ","
        + _longitude_2_decimal_str
        + round_longitude
    )
    return new_topic
