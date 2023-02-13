import boto3
import os
import struct
import math
from CEI_Dynamo_Cache import get_vehicle_by_SN
from CEI_Logging import post_log

client = boto3.client("iot-data", os.environ["AWS_REGION"])
base_url = os.environ["CDF_URL"]

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
            outlist.append(struct.pack("B", num))
        elif num < 65535:
            outlist.append(struct.pack(">H", num))
        else:
            b = (num & 0xFF0000) >> 16
            H = num & 0xFFFF
            outlist.append(struct.pack(">bH", b, H))
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


def lambda_handler(event, context):
    global gpsStatus
    print(f"Event = {event}")
    pub_topic = event.get("topic", "")
    print(f"pub_topic = {pub_topic}")

    # make sure topic is valid
    if "/GTT/CEI/RTVEHDATA" in pub_topic:
        data = event
        # get SN from topic
        # Topic is always SN/messages/json where SN is the serial number of the modem
        split_topic = pub_topic.split("/")
        client_id = split_topic[1]
        print(f"client_id = {client_id}")
        # get data from the cache
        cache_data = get_vehicle_by_SN(client_id)

        print(f"cache_data = {cache_data}")

        gps_data = list(data.values())[0]
        if cache_data is not None:
            if cache_data["CEIVehicleActive"]:
                compile_2100_msg(
                    gps_data,
                    cache_data["vehicleID"],
                    cache_data["vehicleClass"],
                    cache_data["vehicleCityID"],
                    cache_data["agencyID"],
                    cache_data["vehicleSerialNo"],
                    cache_data["CMSID"],
                    cache_data["CEIDeviceID"],
                    cache_data["GTTSerial"],
                )
        else:
            post_log(
                "Unknown",
                "Unknown",
                "Unknown",
                "None",
                "Error",
                "CEI RTRadio Processing",
                "Get Broadcasting Vehicle",
                "Error - Unable to retrieve Broadcasting Vehicle",
            )
            raise Exception("Error - Unable to retrieve Broadcasting Vehicle")
    else:
        post_log(
            "Unknown",
            "Unknown",
            "Unknown",
            "None",
            "Error",
            "CEI RTRadio Processing",
            "Initial Activation",
            "Error - Malformed Topic",
        )
        raise Exception("Error - Malformed Topic")


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
    gpi = gps_data.get("atp.gpi")  # GPIO state - bit masked

    if lat is None or lon is None or hdg is None or spd is None or gpi is None:
        post_log(
            "Unknown",
            "Unknown",
            client_id,
            "None",
            "Error",
            "CEI RTRadio Processing",
            "Message Processing",
            "Error - Malformed GPS Message",
        )
        raise Exception("Error - Malformed GPS Message")

    # process GPS message and create RTRADIO message
    # incoming latitude needs to be converted to degrees/minutes because
    # CMS expects it in that format

    # Raising an Exception if the lat lon values are out of range. Logging the same values as well.
    if (-90 <= lat <= 90) and (-180 <= lon <= 180):
        gps_lat_dddmmmmmm, gps_lon_dddmmmmmm = convert_lat_lon_to_minutes_degrees(
            lat, lon
        )
    else:
        raise Exception(f"Lat: {lat} Lon: {lon} are not in the valid range")

    # IO Mapping
    # IO 1 == ignition
    # IO 2 == left blinker
    # IO 3 == right blinker
    # IO 4 == light bar
    # IO 5 == disable
    # use new GPIO data if available

    gpi = int(gpi)
    # use GPIO information
    ignition = gpi & 0x01
    left_turn = (gpi & 0x02) >> 1
    right_turn = (gpi & 0x04) >> 1  # shift only one for math below
    light_bar = (gpi & 0x08) >> 3
    disable = (gpi & 0x10) >> 4

    # turn status
    turn_status = left_turn
    turn_status |= right_turn

    # op status
    if not ignition or disable:
        op_status = 0
    elif light_bar and ignition and not disable:
        op_status = 1

    # pack up data
    veh_mode_op_turn = turn_status
    veh_mode_op_turn |= op_status << 2
    veh_mode_op_turn |= 0 << 5
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
    # out going topic structure "GTT/GTT/VEH/EVP/2100/2100ET0001/RTRADIO"
    # where second GTT is replaced with the CMS ID
    new_topic = f"GTT/{cms_id.lower()}/VEH/EVP/2100/{gtt_serial}/RTRADIO"

    # Send out new Topic to CMS associated with the client_id
    new_topic = get_2100_topic(message_data, new_topic, cms_id)
    client.publish(topic=new_topic, qos=0, payload=message_data)
    print(
        f"GTT Serial No. is {gtt_serial}, Device Id is {client_id} Agency Id is {agency_id} CMS Id is {cms_id}"  # noqa: E501
    )


def get_2100_topic(
    message,
    pub_topic,
    cms_id,
):

    latitude = message[8:12]
    _latitude = struct.unpack("<i", latitude)[0]

    MINLATITUDE = -90
    MAXLATITUDE = 90

    _dec = _latitude * 0.000001
    _dec_int = math.trunc(_dec)
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
    _longitude = struct.unpack("<i", longitude)[0]

    MINLONGITUDE = -180
    MAXLONGITUDE = 180

    _dec = _longitude * 0.000001
    _dec_int = math.trunc(_dec)
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
    # print (f"_longitude_2_decimal_str = {_longitude_2_decimal_str}")
    # print (f"_long_dec_count = {_long_dec_count}")
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
    print(f" new_topic = {new_topic}")
    return new_topic
