import datetime
import boto3
import pytz
import json
import codecs
import time
import os

from pyspark.sql import SparkSession, SQLContext, DataFrame  # noqa: E402
from pyspark import SparkContext  # noqa: E402
from pyspark.sql.types import *  # noqa: F403, E402

from botocore.awsrequest import AWSRequest  # noqa: E402
from botocore.endpoint import URLLib3Session  # noqa: E402
from botocore.auth import SigV4Auth  # noqa: E402
from botocore.exceptions import ClientError

# configure
spark = SparkSession.builder.master("local").getOrCreate()
sc = SparkContext.getOrCreate()
sqlContext = SQLContext(sc)


# Getting information for script from environment variables.
incoming_bucket_name = os.environ["incoming_bucket_name"]
outgoing_bucket_name = os.environ["outgoing_bucket_name"]
incoming_s3_path = os.environ["whelen_incoming_s3_path"]
outgoing_s3_path = os.environ["whelen_outgoing_s3_path"]
cloudwatch_log_group = os.environ["cloudwatch_log_group"]
cloudwatch_log_stream_name = os.environ["whelen_cloudwatch_log_stream_name"]
cdf_url = os.environ["cdf_url"]

incoming_testing_year = None
incoming_testing_month = None
incoming_testing_day = None


# Local Caching for processing the CDF data
device_dict = {}

aws_region = os.environ["AWS_REGION"]
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(), url=url, data=params, headers=headers
    )  # noqa: E501
    SigV4Auth(
        boto3.Session().get_credentials(), "execute-api", region_name
    ).add_auth(  # noqa: E501
        request
    )
    return URLLib3Session().send(request.prepare()).content


#########################################
# Helper methods to process Whelen Data #
#########################################


def convert_lat_lon_to_minutes_degrees(lat, lon):
    """Converts latitude and longitude in degrees/minutes in a byte format.
    Incoming latitude needs to be converted to degrees/minutes because CMS expects it in that format.

    Args:
        lat (String): Latitude received from the incoming data in string.
        lon (String): Longitude received from the incoming data in string.

    Returns:
        latitude: latitude in byte format, used in creation of RT_Message.
        longitude: longitude in byte format, used in creation of RT_Message.
    """
    return_lat = to_min_degrees(lat)
    return_lon = to_min_degrees(lon)
    return return_lat, return_lon


def to_min_degrees(data) -> bytes:
    """Get a latitude or longitude and get its value in minutes degree.

    Args:
        data (String): data in string. Could be latitude or longitude.

    Returns:
        bytes: location data back in byte format after conversion to minutes degree.
    """
    data = float(data)
    ddd = int(data)
    mmmmmm = float(data - float(ddd)) * 60
    data = (ddd * 1000000 + int(mmmmmm * 10000)) / 1000000
    new_string = hex(int(data * 1000000))
    int_data = int(new_string, 16)
    return_data = int_data.to_bytes(4, byteorder="little", signed=True)
    return return_data


def convert_speed(speed) -> bytes:
    """message sent from device is in kilometers/hour scaled down by 5
    Speed coming from the whelen is in km/h, needs to be converted to
    (meters / 5)/second

    Args:
        speed (String): Received speed from incoming data in string.

    Returns:
        bytes: speed in bytes, used in creation of rt_message.
    """
    if speed is None:
        speed = 0
    new_speed = int(speed * 1000 * 5 / 3600)
    return new_speed.to_bytes(1, byteorder="little", signed=False)


def convert_heading(heading) -> bytes:
    """Heading/Direction is coming from the whelen in degrees, needs to be converted to format of heading per two degrees.

    Args:
        heading (_type_): heading/direction data received from incoming data.

    Returns:
        bytes: heading/direction data in bytes, to be used in rt_message.
    """
    if heading is None:
        heading = 0
    new_heading = int(heading / 2 + 0.5)
    return new_heading.to_bytes(1, byteorder="little", signed=False)


def convert_turn_signal(turn_signal) -> int:
    """Convert turn signal from text format to a literal value.

    Args:
        turn_signal (String): Get turn signal in String.

    Returns:
        int: Turn Signal's value in literal format of either 0, 1, 2 or 3, based on [None, Left, Right, Both] respectively.
    """
    converted_turn_signal = 0  # None
    turn_signal = turn_signal.lower()
    if turn_signal == "left":
        converted_turn_signal = 1
    elif turn_signal == "right":
        converted_turn_signal = 2
    elif turn_signal == "both":
        converted_turn_signal = 3
    return converted_turn_signal


def get_op_status(enable, disable) -> int:
    """Get OP_Status value based on Enable, Disable Fields.

    Args:
        enable (String): Get enable value in String as true or false.
        disable (String): Get disable value in String as true or false.

    Returns:
        int: Op status is either 0, 1.
        Corresponding to: op_status as: - 0: Disabled
                                        - 1: Enabled
    """
    op_status = 0  # disabled
    enable = enable.lower()
    if disable == "true":
        op_status = 0
    elif enable == "true" and disable == "false":
        op_status = 1
    return op_status


########################################################
# Helper Methods for this PySpark Script #
########################################################


def upload_cloudwatch_log(message) -> None:
    """Upload a log message to cloudwatch logs.

    Args:
        message (String): message to upload to cloudwatch log stream.
    """
    log_client = boto3.client("logs", region_name=aws_region)
    desc_response = log_client.describe_log_streams(
        logGroupName=cloudwatch_log_group,
        logStreamNamePrefix=cloudwatch_log_stream_name,
    )
    ts = int(time.time()) * 1000
    try:
        log_client.put_log_events(
            logGroupName=cloudwatch_log_group,
            logStreamName=cloudwatch_log_stream_name,
            logEvents=[
                {"timestamp": ts, "message": message},
            ],
            sequenceToken=desc_response["logStreams"][0][
                "uploadSequenceToken"
            ],  # noqa: E501
        )
    except KeyError as ke:
        log_client.put_log_events(
            logGroupName=cloudwatch_log_group,
            logStreamName=cloudwatch_log_stream_name,
            logEvents=[
                {"timestamp": ts, "message": message + "error: " + str(ke)},
            ],
        )


def unread_objects_s3() -> list:
    """Read the unread incoming messages in the S3 bucket under today's date.

    Returns:
        list: A list of unread objects to process later.
    """
    # 1. Connect to S3 bucket.
    # 2. Find year, month and date from today's date.
    # 3. Create a 'path_string' to access a folder in s3 bucket.
    # 4. Filter S3 objects which do not have the tag "Read", indicating this object is still not processed.

    # 1
    s3_client = boto3.client("s3", region_name=aws_region)
    s3 = boto3.resource("s3")
    my_bucket = s3.Bucket(incoming_bucket_name)

    # 2
    today = datetime.datetime.utcnow()

    year = (
        str(today.year) if incoming_testing_year is None else str(incoming_testing_year)
    )  # noqa: E501
    month = (
        str(today.month)
        if incoming_testing_month is None
        else str(incoming_testing_month)
    )  # noqa: E501
    day = (
        str(today.day)
        if incoming_testing_day is None
        else str(incoming_testing_day)  # noqa: E501
    )  # noqa: E501

    # 3
    obj_path = (
        f"{incoming_s3_path}/{year}/{month.zfill(2)}/{day.zfill(2)}"  # noqa: E501
    )
    not_read_objects = []

    # 4
    for object_summary in my_bucket.objects.filter(Prefix=f"{obj_path}"):
        key = object_summary.key
        response = s3_client.get_object_tagging(
            Bucket=incoming_bucket_name, Key=key
        )  # noqa: E501
        try:
            # Check if a tag exists.
            response["TagSet"][0]["Key"]
        except:  # noqa: E722
            not_read_objects.append(key)
            continue
    return not_read_objects


def tag_read_s3_objects() -> None:
    """This will be done after the processing, and it will tag the processed object with a "Read", indicating we've processed this object."""

    # 1. Find unread objects list.
    # 2. For each object, put the tag "Read".
    unread_objects = unread_objects_s3()
    s3_client = boto3.client("s3", region_name=aws_region)
    for obj in unread_objects:
        s3_client.put_object_tagging(
            Bucket=incoming_bucket_name,
            Key=obj,
            Tagging={"TagSet": [{"Key": "Read", "Value": ""}]},
        )
    # Optional: A message that indicates we've processed this object.
    upload_cloudwatch_log("Read objects tagged in S3 bucket for object: " + obj)


def fetch_s3data() -> DataFrame:
    """Go into S3 and store the incoming 'unprocessed' message as a DataFrame.

    Returns:
        DataFrame: Get the processed pyspark's dataframe from S3, which would be a List of PySpark.Rows
    """
    # 1. Get a list of unread objects from S3.
    # 2. Create the local directories "incoming_whelen_msg_local_copy" and "processed_whelen_msg_local_copy", which will store the respective files locally.
    # 3. Iterate over the array and download each file from S3 into the incoming messages folder locally.
    # 4. Get Processed DataFrame of the objects, which will be later used to create rt_message.

    s3 = boto3.client("s3", region_name=aws_region)
    # 1
    unread_array = unread_objects_s3()
    if len(unread_array) == 0:
        upload_cloudwatch_log("No new Unread files found today")
        os._exit(os.EX_OK)
    final_str = ""
    new_array = ["["]

    # 2
    if not os.path.exists("incoming_whelen_msg_local_copy"):
        os.mkdir("incoming_whelen_msg_local_copy")
    if not os.path.exists("processed_whelen_msg_local_copy"):
        os.mkdir("processed_whelen_msg_local_copy")
    for obj in unread_array:
        filename = obj.split("/")[
            -1
        ]  # Take the filename and use it to write locally  # noqa: E501
        # 3
        s3.download_file(
            incoming_bucket_name,
            obj,
            f"incoming_whelen_msg_local_copy/{filename}.txt",
        )  # noqa: E501
        # local testing && s3 testing supported
        rdd = sc.textFile(f"incoming_whelen_msg_local_copy/{filename}.txt")

        for i in range(0, len(rdd.collect())):
            new_array += rdd.collect()[i]
    del new_array[-1]
    new_array.append("]")
    final_str += "".join(new_array)
    # 4
    processed_df = spark.read.json(sc.parallelize([final_str]))
    return processed_df


#########################################################
#########################################################


def create_message(message_details):
    """Creates an RT_Message based on all the information received from incoming_message and CDF.

    Args:
        message_details (dict): a dictionary of all fields combined from CDF and incoming_message.

    Returns:
        rt_message -> multiple values returned that makes up an rt_message.
    """

    vehicle_city_id_bytes = int(message_details["vehicleCityID"]).to_bytes(
        1, byteorder="little", signed=False
    )

    vehicle_class_bytes = int(message_details["vehicleClass"]).to_bytes(
        1, byteorder="little", signed=False
    )

    vehicle_id_bytes = int(message_details["vehicleID"]).to_bytes(
        2, byteorder="little", signed=False
    )

    unit_id_bytes = int(message_details["vehicleSerialNo"]).to_bytes(
        4, byteorder="little", signed=False
    )

    lat = message_details["latitude"]
    lon = message_details["longitude"]
    hdg = message_details["direction"]  # Current heading/direction
    spd = message_details["speed"]  # Current speed kmph
    stt = message_details["gstt"]  # GPS fix status (0 = no fix, 1 = fix)
    # 1 in case of Whelen, This can be set later. Right now passing the value manually.

    # process GPS message and create RTRADIO message
    gps_lat_dddmmmmmm, gps_lon_dddmmmmmm = convert_lat_lon_to_minutes_degrees(lat, lon)

    turn_status = message_details["turn_signal"]

    # pack up data
    veh_mode_op_turn = turn_status
    veh_mode_op_turn |= message_details["op_status"] << 2
    veh_mode_op_turn |= int(message_details["vehicleMode"]) << 5
    veh_mode_op_turn = veh_mode_op_turn.to_bytes(
        1, byteorder="little", signed=False
    )  # noqa: E501

    velocity_mpsd5 = convert_speed(spd)
    hdg_deg2 = convert_heading(hdg)
    gps_status = stt
    gpsc_stat = gps_status.to_bytes(2, byteorder="little", signed=False)
    # whelen does not provide rssi information set to 0
    vehicle_rssi = b"\x00\x00"
    # filler
    padding = b"\x00\x00"
    # CMS can go to CDF to get this info directly
    satellite_gps = b"\x00\x00\x00\x00"
    conditional_priority = b"\x00"
    # modem has no slot
    veh_diag_value = b"\x00\x00\x00\x00"

    # assemble message
    rt_message_data = (
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
    rssi = int.from_bytes(vehicle_rssi, byteorder="little")
    veh_gps_satellite = int.from_bytes(satellite_gps, byteorder="little")
    conditional_priority = int.from_bytes(
        conditional_priority, byteorder="little"
    )  # noqa: E501
    veh_diag_value = int.from_bytes(veh_diag_value, byteorder="little")
    rt_message_data = str(codecs.encode(rt_message_data, "base64"), "utf-8")
    device_timestamp = time.strftime(
        "%m/%d/%Y %H:%M:%S",
        time.localtime(float(message_details["device_timestamp"]) / 1000),
    )
    iot_timestamp = time.strftime(
        "%m/%d/%Y %H:%M:%S",
        time.localtime(float(message_details["iot_timestamp"]) / 1000),
    )

    return (
        message_details["CMSID"],
        str(message_details["GTTSerial"]),
        int(message_details["vehicleSerialNo"]),  # unit id
        rssi,
        lat,  # Current latitude
        lon,  # Current longitude
        hdg,  # Current heading
        spd,  # Current speed kmph
        gps_status,
        veh_gps_satellite,
        int(message_details["vehicleID"]),
        int(message_details["vehicleCityID"]),
        int(message_details["vehicleMode"]),
        int(turn_status),
        int(message_details["op_status"]),
        int(message_details["vehicleClass"]),
        conditional_priority,
        float(veh_diag_value),
        message_details["agencyID"],
        str(message_details["vehicleName"]),
        message_details["client_id"],
        device_timestamp,
        iot_timestamp,
        rt_message_data,
    )


def append_cdf_info(message_details, client_id) -> dict:
    """Append CDF details that are stored in cache to the message dict.

    Args:
        message_details (dict): message details used to create rt_message.
        client_id (String): to access a particular record in cache.

    Returns:
        dict: the complete message details as dict needed to create an rt_message.
    """
    try:
        message_details = {**message_details, **device_dict[client_id.lower()]}
    except Exception as e:
        upload_cloudwatch_log("Error in appending CDF information: " + str(e))
    return message_details


def get_details_from_cdf(client_id) -> bool:
    """Get details from CDF for a particular Client ID and store it in the local cache's device_dict.
    The values from this device_dict would be used later to create rt_message.

    Args:
        client_id (String): Client ID in string. Poll CDF to get information about this client.

    Returns:
        bool:   True -> if successfully entered information in device_cache.
                False -> There was some error in processing, not entered in local cache.
    """

    # Assemble URL for communicator
    try:
        url = f"{cdf_url}/devices/{client_id.lower()}"
        code = send_request(url, "GET", region_name=aws_region, headers=headers)
        if code:
            communicator_data = json.loads(code)
            # check to see if communicator
            template_id = communicator_data.get("templateId")
            if not template_id:
                return False

            if template_id == "integrationcom":
                # get region and agency name from device CDF data
                groups = communicator_data.get("groups")

                if groups:
                    out = groups.get("out")
                else:
                    return False

                # sometimes device data has out
                # sometimes it doesn't; handle both cases
                if out:
                    ownedby = out.get("ownedby")
                else:
                    ownedby = groups.get("ownedby")

                agency = ownedby[0].split("/")[2]
                region = ownedby[0].split("/")[1]

                # get attributes from communicator CDF data
                communicator_attributes = communicator_data.get("attributes")
                if not communicator_attributes:
                    return False

                gtt_serial = communicator_attributes.get("gttSerial")
                if not gtt_serial:
                    return False

                mac_address = communicator_attributes.get("addressMAC")
                if not mac_address:
                    return False

                # use communicator data to get vehicle data
                devices = communicator_data.get("devices")

                if devices:
                    devices_in = devices.get("in")
                if not devices:
                    return False

                # sometimes device data has out
                # sometimes it doesn't; handle both cases
                if devices_in:
                    installedat = devices_in.get("installedat")
                else:
                    installedat = devices.get("installedat")

                vehicle = installedat[0]

                # Assemble URL for vehicle
                url = f"{cdf_url}/devices/{vehicle.lower()}"

                code = send_request(
                    url, "GET", region_name=aws_region, headers=headers
                )  # noqa: E501
                vehicle_data = json.loads(code)
                vehicle_attributes = vehicle_data.get("attributes")
                if not vehicle_attributes:
                    return False

                # use communicator data to get agency data
                url = f"{cdf_url}/groups/%2F{region}%2F{agency}"

                code = send_request(
                    url, "GET", region_name=aws_region, headers=headers
                )  # noqa: E501

                agency_data = json.loads(code)
                agency_attributes = agency_data.get("attributes")
                if not agency_attributes:
                    return False

                agency_code = agency_attributes.get("agencyCode")
                if not agency_code:
                    return False

                agency_id = agency_attributes.get("agencyID")

                cms_id = agency_attributes.get("CMSId")
                if not agency_id:
                    return False

                if not cms_id:
                    return False

                mac_address = mac_address.replace(":", "")[-6:]
                try:
                    unit_id_binary = bin(int(mac_address, 16))[2:].zfill(24)

                    orrer = f"{8388608:024b}"
                    orred_unit_id = ""

                    for i in range(0, 24):
                        orred_unit_id += str(
                            int(orrer[i]) | int(unit_id_binary[i])
                        )  # noqa: E501

                    unit_id = int(orred_unit_id, 2)
                except:  # noqa: E722
                    return False

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
                    return False

                device_dict[client_id.lower()] = {
                    "ID": client_id,
                    "vehicleID": vehicle_id,
                    "vehicleClass": vehicle_class,
                    "vehicleCityID": vehicle_city_id,
                    "agencyID": agency_id,
                    "GTTSerial": gtt_serial,
                    "CMSID": cms_id,
                    "vehicleSerialNo": unit_id,
                    "vehicleMode": vehicle_mode,
                    "vehicleName": vehicle,
                }
                # At this point all the information from CDF is filled in this local cache.
                return True
        else:
            return False
    except Exception as e:
        upload_cloudwatch_log(
            "Error in getting details from CDF for client id: {}, with error: {}".format(
                client_id, e
            )
        )
        return False


def retrieve_large_data(data):
    """Get all information from the incoming data, append CDF information for each message and convert each message in form of a RT_Message.
    We simply access each value through its column-name.

    Args:
        data (List of PySpark's Row): incoming data in form of pyspark's row.

    Returns:
        tuple: of RT_message which contains various fields to convey information about the message.
    """

    # Get all information from the data.
    enable = "true" if data["enable"] == "True" else "false"
    disable = "true" if data["disable"] == "True" else "false"
    op_status = get_op_status(enable, disable)

    gps = data["gps"]
    direction = int(gps["direction"])
    speed = float(gps["speed"])
    latitude = float(gps["latitude"])
    longitude = float(gps["longitude"])

    turn_signal = convert_turn_signal(data["turnSignal"])
    device_timestamp = data["device_timestamp"]
    iot_timestamp = data["iot_timestamp"]

    # We are directly getting the client id in the topic from the lambda.
    client_id = data["topic"]
    gstt = 1  # NOTE: GPS Status is 1 in case of Whelen. This can be set later. Right now passing the value manually.

    # Create a dict of one message that will contain all information related to the message.

    # By default it will contain information from incoming_message.
    # We will append additional information from CDF as well.
    message_details = {
        "direction": direction,
        "latitude": latitude,
        "longitude": longitude,
        "speed": speed,
        "gstt": gstt,
        "turn_signal": turn_signal,
        "op_status": op_status,
        "device_timestamp": device_timestamp,
        "iot_timestamp": iot_timestamp,
        "client_id": client_id,
    }

    # This message is created by default. Will be overriden below.
    rt_message = (
        "No related Device found in CDF",
        "Error",
        1,
        1,
        latitude,
        longitude,
        direction,
        speed,
        0,  # atp_gstt,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1.0,
        "Error",
        "Error",
        "Error",
        device_timestamp,
        iot_timestamp,
        "Error",
    )  # noqa: E501

    if client_id.lower() in device_dict:
        # Use from cache if already there.
        # Append the additional CDF fields to the message details.
        message_details = append_cdf_info(message_details, client_id)
        rt_message = create_message(message_details)
    else:
        # Get details from CDF and append those fields to message details.
        success = get_details_from_cdf(client_id)
        if success:
            message_details = append_cdf_info(message_details, client_id)
            rt_message = create_message(message_details)
        else:
            upload_cloudwatch_log(
                "Error in getting details from CDF for client: " + client_id
            )
    return rt_message


def process_data() -> DataFrame:
    """Convert all the messages received in a consistent format.

    Returns:
        DataFrame: of processed messages.
    """

    # 1. Get the processed dataframe from S3
    # 2. Use each Row to create an Individual DataFrame and adds value of each message.
    # 3. Create a schema and align each message in this particular schema.
    # 4. Create a DataFrame of the processed messages.

    # 1
    df = fetch_s3data()

    # 2
    large_df = df.rdd.flatMap(lambda x: (retrieve_large_data(x),))

    # 3
    schema = StructType(  # noqa: F405
        [
            StructField("CMSId", StringType(), True),  # noqa: F405, E501
            StructField("GTTSerial", StringType(), True),  # noqa: F405, E501
            StructField("UnitId", IntegerType(), True),  # noqa: F405, E501
            StructField("rssi", IntegerType(), True),  # noqa: F405, E501
            StructField("Latitude", DoubleType(), True),  # noqa: F405, E501
            StructField("Longitude", DoubleType(), True),  # noqa: F405, E501
            StructField("Heading", IntegerType(), True),  # noqa: F405, E501
            StructField("Speed", FloatType(), True),  # noqa: F405, E501
            StructField("VehicleGPSCStat", IntegerType(), True),  # noqa: F405, E501
            StructField(  # noqa: F405, E501
                "VehicleGPSCSatellites", IntegerType(), True  # noqa: F405, E501
            ),
            StructField("VehicleVID", IntegerType(), True),  # noqa: F405, E501
            StructField("AgencyCode", IntegerType(), True),  # noqa: F405, E501
            StructField("VehicleModeStatus", IntegerType(), True),  # noqa: F405, E501
            StructField("VehicleTurnStatus", IntegerType(), True),  # noqa: F405, E501
            StructField("VehicleOpStatus", IntegerType(), True),  # noqa: F405, E501
            StructField("VehicleClass", IntegerType(), True),  # noqa: F405, E501
            StructField("ConditionalPriority", IntegerType(), True),  # noqa: F405, E501
            StructField(  # noqa: F405, E501
                "VehicleDiagnosticValue", DoubleType(), True  # noqa: F405, E501
            ),
            StructField("AgencyID", StringType(), True),  # noqa: F405, E501
            StructField("VehicleName", StringType(), True),  # noqa: F405, E501
            StructField("DeviceName", StringType(), True),  # noqa: F405, E501
            StructField("device_timestamp", StringType(), True),  # noqa: F405, E501
            StructField("ioT_timestamp", StringType(), True),  # noqa: F405, E501
            StructField("OriginalRTRadioMsg", StringType(), True),  # noqa: F405, E501
        ]
    )

    # 4
    return_df = sqlContext.createDataFrame(large_df, schema)

    return return_df


def upload_directory(path, bucketname, s3_objPath) -> bool:
    """Upload the processed file in S3.

    Args:
        path (String): Local path of the processed messages file.
        bucketname (String): S3 bucket name to store the parquet file.
        s3_objPath (String): Path in s3 to store the parquet file.

    Returns:
        bool: True -> Successfully stored the file in S3.
              False -> Error in storing file in S3.
    """
    s3 = boto3.resource("s3")
    for root, _, files in os.walk(path):
        for file in files:
            try:
                s3.meta.client.upload_file(
                    os.path.join(root, file),
                    bucketname,
                    str(s3_objPath + "/" + file),  # noqa: E501
                )
            except ClientError as e:
                upload_cloudwatch_log(str(e))
                return False
    return True


def write_by_agency_id():
    """Walk through the processed messages local directory and upload the processed messages 'parquet' file to S3 for a particular agency."""

    # In case of Whelen the Agency ID will be a "NULL_GUID".

    # today's datetime
    today = datetime.datetime.utcnow()
    pacific = pytz.timezone("US/Pacific")
    d = datetime.datetime.now(pacific)
    central = pytz.timezone("US/Central")
    time = d.astimezone(central)

    # aws testing
    month = str(today.month)
    day = str(today.day)
    hour = str(time.hour - 5)  # Actual Central time

    # Upload the files to S3 from the local environment
    for _, dirs, _ in os.walk("processed_whelen_msg_local_copy"):
        if len(dirs) != 0:
            for id_folder in dirs:
                agency_id = id_folder.split("=")[1]
                s3_filePath = f"{outgoing_s3_path}/{agency_id}/{today.year}/{month.zfill(2)}/{day.zfill(2)}/{hour.zfill(2)}"  # noqa: E501
                upload_directory(
                    f"processed_whelen_msg_local_copy/{id_folder}",
                    outgoing_bucket_name,
                    s3_filePath,  # noqa: E501
                )  # noqa: E501

    upload_cloudwatch_log("Written processed message to s3")


def write_back_to_s3():
    """1. Get the final processed data's dataframe,
    2. create a parquet file and store it in the local processed messages folder.
    3. call method to write this file to s3.
    4. tag the incoming message in s3 as read.
    """

    # 1.
    final_df = process_data()
    # 2.
    final_df.write.partitionBy("AgencyID").mode("overwrite").parquet(
        "processed_whelen_msg_local_copy"
    )  # noqa: E501

    # 3.
    write_by_agency_id()

    # 4.
    tag_read_s3_objects()


write_back_to_s3()
