import time
import redis
from json import loads
from json import dumps
from math import trunc
from struct import pack
from struct import unpack
from boto3 import client
from boto3 import Session
from os import environ
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
import threading
import uuid
import os, sys

queue = []
threads = []

sqs_client = client("sqs")


def send_sqs_message(msg_body, msg_group_id, msg_id):
    """Send the incoming incident message to the SQS

    Args:
        QueueName (string): what queue we're talking about
        msg_body (string): body of message being processed
        msg_group_id (uuid): message group being queued (prevents double processing)
        msg_id (uuid): specific message being queued

    Returns:
        response: results of all operations
    """

    # Send the SQS message
    sqs_queue_url = sqs_client.get_queue_url(QueueName="whelen-analytics.fifo")[
        "QueueUrl"
    ]

    try:
        msg = sqs_client.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=dumps(msg_body),
            MessageGroupId=f"{uuid.uuid4()}",
            MessageDeduplicationId=f"{uuid.uuid4()}",
        )
    except Exception as e:
        print(f"[ERROR] - SQS Send: {e}")
        return None
    return msg


client = client("iot-data", environ["AWS_REGION"])
base_url = environ["CDF_URL"]

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}


# redis_address = "kun-el-141dv6idlb2s1.ibjafd.0001.use1.cache.amazonaws.com"     #redis_cache
# redis_port = 6379

# redis_cache = redis.Redis(host=redis_address, port=redis_port, db=0, charset="utf-8", decode_responses=True)      #redis_cache

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


def connectToRedis():
    # print("connecting to Redis...")
    try:
        # These two parameters below needs to be set in the environment variable.
        redis_address = environ["RedisEndpointAddress"]  # redis_cache
        redis_port = environ["RedisEndpointPort"]
        # the parameter -> "utf-8" allows to convert to Unicode, since Redis returns binary Data.
        cache = redis.Redis(
            host=redis_address,
            port=redis_port,
            db=0,
            charset="utf-8",
            decode_responses=True,
        )  # redis_cache
        return cache
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(f"[ERROR] - {e}")


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
    # print(f"Requesting... {url}  {method}")
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


def processMessage(message, event):
    attributes = message["attributes"]
    data = loads(message["body"])
    # print(f"Data Loaded {data}")
    # get SN from topic
    client_id = data.get("DeviceId")
    cache = connectToRedis()
    # print(f"Redis Connected")
    # get data from the cache
    try:
        #  print(client_id.lower())
        redis_cache_data = cache.hgetall(client_id.lower())  # redis_cache
        print("Cache data got")
        # Epoch time is used for the key
        time = attributes["SentTimestamp"]
        dataVal = data.get("GPS", None)
        if not dataVal:
            dataVal = data.get("msgData")
        gps_data = loads(dataVal)
        #  print("gpsData Loaded")
        start_time = gps_data.get("timeAt")

        if redis_cache_data:
            # print("compilation in progress...")
            print(f'GPIO Data from Cache = {redis_cache_data["GPIO"]}')
            compile_2100_msg(
                gps_data,
                redis_cache_data["GPIO"],
                redis_cache_data["vehicleID"],
                redis_cache_data["vehicleClass"],
                redis_cache_data["vehicleCityID"],
                redis_cache_data["agencyID"],
                redis_cache_data["vehicleSerialNo"],
                redis_cache_data["CMSID"],
                redis_cache_data["ID"],
                redis_cache_data["GTTSerial"],
                redis_cache_data["vehicleMode"],
                start_time,
                time,
                data,
            )
        else:
            #  print("GPIO/redis value NOT FOUND - getting from CDF...")
            # Assemble URL for communicator
            url = f"{base_url}/devices/{client_id.lower()}"
            code = send_request(url, "GET", environ["AWS_REGION"], headers=headers)

            try:
                communicator_data = loads(code)
                print(f"Code val = {communicator_data}")
            except:
                print(f"{url} not found")
                return
            # check to see if communicator
            template_id = str(communicator_data.get("templateId", None))
            if not template_id:
                print("[ERROR]No template id in device CDF data")
                return

            template_id = template_id
            # Only work with SCP vehicle modems
            if template_id == "integrationcom":
                # get region and agency name from device CDF data
                groups = communicator_data.get("groups")

                if groups:
                    out = groups.get("out")
                else:
                    print("[ERROR]No groups in communicator CDF data")
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
                    print("[ERROR]No attributes value in communicator CDF data")
                    return

                # if using the IntegrationCom template, check for the state of the preemption licence. If anything other than "active", return.
                if template_id == "integrationcom":
                    if not communicator_attributes.get("preemptionLicense") == "active":
                        return

                gtt_serial = communicator_attributes.get("gttSerial")
                if not gtt_serial:
                    print("[ERROR]No gtt_serial value in attributes")
                    return

                mac_address = communicator_attributes.get("addressMAC")
                if not mac_address:
                    print("[ERROR]No MAC address value in attributes")
                    return
                # use communicator data to get vehicle data
                devices = communicator_data.get("devices")

                if devices:
                    devices_in = devices.get("in")
                if not devices:
                    print("[ERROR]No associated vehicle in communicator CDF data")
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

                vehicle_data = loads(code)
                vehicle_attributes = vehicle_data.get("attributes")
                if not vehicle_attributes:
                    print("[ERROR]No attributes value in vehicle CDF data")
                    return
                # use communicator data to get agency data
                url = f"{base_url}/groups/%2F{region}%2F{agency}"

                code = send_request(
                    url, "GET", environ["AWS_REGION"], headers=headers
                )  # noqa: E501

                agency_data = loads(code)
                agency_attributes = agency_data.get("attributes")
                if not agency_attributes:
                    print("[ERROR]No attributes value in Agency json string")
                    return
                agency_code = agency_attributes.get("agencyCode")
                if not agency_code:
                    print("[ERROR]Agency Code not found in CDF")
                    return
                agency_id = agency_attributes.get("agencyID")
                cms_id = agency_attributes.get("CMSId")
                if not agency_id:
                    print("[ERROR]Agency ID (GUID) not found in CDF")
                    return
                if not cms_id:
                    print("[ERROR]CMS ID (GUID) not found in CDF")
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
                    print("[ERROR]MAC address is not numeric")
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

                placeholder = {
                    "Ignition": True,
                    "LeftTurn": False,
                    "RightTurn": False,
                    "Enabled": True,
                    "DisabledMode": False,
                }

                gps_data["GPIO"] = vehicle_attributes.get("GPIO", dumps(placeholder))
                if not gps_data["GPIO"]:
                    print("[ERROR] No GPIO data - USING DEFAULT PLACEHOLDER")

                # get Class from CDF
                vehicle_class = vehicle_attributes.get("class")
                if not vehicle_class:
                    print("[ERROR] No class in device attributes")
                    return

                compile_2100_msg(
                    gps_data,
                    gps_data["GPIO"],
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
                    time,
                    data,
                )
                insert_in_cache(
                    client_id.lower(),
                    vehicle_id,
                    vehicle_class,
                    vehicle_city_id,
                    agency_id,
                    gtt_serial,
                    gps_data["GPIO"],
                    cms_id,
                    unit_id,
                    vehicle_mode,
                    cache,
                )
            else:
                print("[ERROR]communicator does not have templateId; exiting ")
                return
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(f"[ERROR] - {e}")


def get_time(val):
    return val.get("time")


def lambda_handler(event, context):
    # print('Starting...')

    if not event.get("Records"):
        # print("no records")
        return
    queue.clear()
    print("QueueCleared")
    for message in event["Records"]:
        # print(f"processing {message}")
        # processMessage(message, event)
        thread = threading.Thread(target=processMessage, args=(message, event))
        thread.start()
        threads.append(thread)

    for x in threads:
        x.join()

    queue.sort(key=get_time)

    for x in queue:
        client.publish(topic=x.get("topic"), qos=0, payload=x.get("data"))
    # print(f"Published - {x.get('topic')}")

    # Analytics Processing - deactive for now
    if False:
        for x in queue:
            msg = x.get("msg_data")
            msg["topic"] = x.get("topic").split(".")[1]
            msg["iot_timestamp"] = x.get("time")
            msg["device_timestamp"] = x.get("messageid")
            send_sqs_message(
                msg, msg["topic"], f'{msg["topic"]}_{msg["iot_timestamp"]}'
            )
            # print(f"SQS Response = {resp}")


def compile_2100_msg(
    gps_data,
    gpio_data,
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
    timestamp,
    msg_data,
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
    print(f"GPIO Data = {gpio_data}")
    lat = gps_data.get("latitude")  # Current latitude
    lon = gps_data.get("longitude")  # Current longitude
    hdg = gps_data.get("heading")  # Current heading
    spd = gps_data.get("speed")  # Current speed kmph

    stt = 1  # GPS fix status (0 = no fix, 1 = fix)
    # gpi = gpio_data  # GPIO state - bit masked
    # gps_en = gps_data.get("enable", None)

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

    try:
        # gpi = 0
        gpio_data = loads(gpio_data)
        # use GPIO information
        ignition = gpio_data.get("Ignition")
        left_turn = 0  # (gpi & 0x02) >> 1
        right_turn = 0  # (gpi & 0x04) >> 1  # shift only one for math below
        light_bar = 1  # gpio_data.get("Enabled")
        # disable = 0  # gpio_data.get("DisabledMode")
        # turnSignal = 0

        if gpio_data.get("LeftTurn"):
            print(f'Left Turn = {gpio_data.get("LeftTurn")}')
            left_turn = 1

        if gpio_data.get("RightTurn"):
            print(f"Right Turn = {gpio_data.get('RightTurn')}")
            right_turn = 2

        # turn status
        turn_status = left_turn
        turn_status |= right_turn
        print(f"turn_status = {turn_status}")
        # op status

        print(f'Lightbar = {gpio_data.get("Enabled")}')
        print(f'Ignition = {gpio_data.get("Ignition")}')
        op_status = 0
        if not ignition:
            op_status = 0
            print(f"Ignition = {gpio_data.get('Ignition')}")
        elif light_bar and ignition:
            op_status = 1
        print(op_status)
    # try:
    #    if not gps_en:
    #        op_status = 0
    # except Exception as e:
    #     exc_type, exc_obj, exc_tb = sys.exc_info()
    #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #      print(exc_type, fname, exc_tb.tb_lineno)
    #      print(f"[ERROR] - {e}")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
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
    # print(f"message data = {unit_id_bytes} {vehicle_rssi} {padding} {gps_lat_dddmmmmmm} {gps_lon_dddmmmmmm} {velocity_mpsd5} {hdg_deg2} {gpsc_stat} {satellite_gps} {vehicle_id_bytes} {vehicle_city_id_bytes} {veh_mode_op_turn} {vehicle_class_bytes} {conditional_priority} {padding} {veh_diag_value}")
    # out going topic structure "GTT/GTT/VEH/EVP/2100/2100ET0001/RTRADIO"
    # where second GTT is replaced with the CMS ID
    new_topic = f"GTT/{cms_id.lower()}/VEH/EVP/2100/{gtt_serial}/RTRADIO"

    # Send out new Topic to CMS associated with the client_id
    try:
        new_topic = get_2100_topic(message_data, new_topic, cms_id)
        print(f"topic = {new_topic}")
        queue.append(
            {
                "time": start_time,
                "topic": new_topic,
                "data": message_data,
                "messageid": timestamp,
                "msg_data": msg_data,
            }
        )

        print(
            f"GTT Serial No. is {gtt_serial}, Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id}"
        )
    # print(f"GTT Serial No. is {gtt_serial}, Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id}"  # noqa: E501
    # )
    except Exception as e:
        print(f"[ERROR] Queue FAIL {e}")


def insert_in_cache(
    client_id,
    vehicle_id,
    vehicle_class,
    vehicle_city_id,
    agency_id,
    gtt_serial,
    GPIO,
    cms_id,
    unit_id,
    vehicle_mode,
    cache,
):
    try:
        print(f"GPIO = {GPIO}")
        current_time = int(time.time())
        item = {
            "ID": client_id,
            "vehicleID": vehicle_id,
            "vehicleClass": vehicle_class,
            "vehicleCityID": vehicle_city_id,
            "agencyID": agency_id,
            "GTTSerial": gtt_serial,
            "GPIO": GPIO,
            "CMSID": cms_id,
            "vehicleSerialNo": unit_id,
            "vehicleMode": vehicle_mode,
            "ExpirationTime": current_time + 1200,
        }

        cache.hmset(client_id, item)  # redis_cache
    except Exception as e:
        print(f"Insertion Failure - {e}")


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
    _latitude_2_decimal_str = str(_latitude_2_decimal)

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
    _longitude_2_decimal_str = str(_longitude_2_decimal)

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
