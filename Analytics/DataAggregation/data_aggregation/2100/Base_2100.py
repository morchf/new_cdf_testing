import base64
import codecs
import json
import struct

from pyspark.sql import DataFrame
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from data_aggregation.Utils.AwsUtil import (
    fetch_s3data,
    send_request,
    upload_cloudwatch_log,
)
from data_aggregation.Utils.Common import append_cdf_info

from .DataProcessor import (
    decode_heading,
    decode_op_turn_status,
    decode_speed,
    display_latitude_from_raw,
    display_longitude_from_raw,
)

__all__ = [
    "create_message",
    "get_details_from_cdf",
    "retrieve_large_data",
    "process_data",
]


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
    message = (
        message_details["message"][:24]
        + vehicle_id_bytes
        + message_details["message"][26:28]
        + vehicle_class_bytes
        + message_details["message"][29:]
    )  # noqa: E501

    final_message = message[:26] + vehicle_city_id_bytes + message[27:]

    unit_id = int.from_bytes(final_message[0:4], byteorder="little")  # vehSN

    rssi = int.from_bytes(final_message[4:6], byteorder="little")

    gps_lat_dddmmmmmm = display_latitude_from_raw(
        struct.unpack("<i", final_message[8:12])[0]
    )  # noqa: E501

    gps_lon_dddmmmmmm = display_longitude_from_raw(
        struct.unpack("<i", final_message[12:16])[0]
    )  # noqa: E501

    spd = decode_speed(final_message[16:17])

    hdg = decode_heading(final_message[17:18])

    gps_status = int.from_bytes(final_message[18:20], byteorder="little")

    # ! Temporary fix to handle one-hot-encoded satellite count treated as signed int
    veh_gps_satellite = min(
        int.from_bytes(final_message[20:24], byteorder="little"),
        2147483647,
    )

    vehicle_mode, op_status, turn_status = decode_op_turn_status(
        int.from_bytes(final_message[27:28], byteorder="little")
    )

    conditional_priority = int.from_bytes(
        final_message[29:30], byteorder="little"
    )  # noqa: E501

    (veh_diag_value,) = struct.unpack("f", final_message[32:36])

    final_message = str(codecs.encode(final_message, "base64"), "utf-8")

    device_timestamp = "No_device_timestamp"

    return (
        message_details["CMSID"],
        str(message_details["GTTSerial"]),
        unit_id,
        rssi,
        float(gps_lat_dddmmmmmm),
        float(gps_lon_dddmmmmmm),
        hdg,
        spd,
        gps_status,
        veh_gps_satellite,
        int(message_details["vehicleID"]),
        int(message_details["vehicleCityID"]),
        vehicle_mode,
        turn_status,
        op_status,
        int(message_details["vehicleClass"]),
        conditional_priority,
        float(veh_diag_value),
        message_details["agencyID"],
        str(message_details["vehicleName"]),
        message_details["client_id"],
        device_timestamp,
        message_details["iot_timestamp"],
        final_message,
    )


def get_details_from_cdf(client_id, awsConfig, envConfig) -> bool:
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
        url = f"{envConfig.cdf_url}/devices/{client_id.lower()}"
        code = send_request(
            url,
            "GET",
            region_name=awsConfig["aws_region"],
            headers=awsConfig["headers"],
        )
        if code:
            communicator_data = json.loads(code)
            # check to see if communicator
            template_id = communicator_data.get("templateId")
            if not template_id:
                return False

            # Only work with SCP vehicle modems
            if template_id == "communicator":
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
                url = f"{envConfig.cdf_url}/devices/{vehicle.lower()}"

                vehicle_cdf_data = send_request(
                    url,
                    "GET",
                    region_name=awsConfig["aws_region"],
                    headers=awsConfig["headers"],
                )  # noqa: E501
                if not vehicle_cdf_data:
                    upload_cloudwatch_log("No vehicle_cdf_data", awsConfig, envConfig)
                    return False
                vehicle_data = json.loads(vehicle_cdf_data)
                vehicle_attributes = vehicle_data.get("attributes")
                if not vehicle_attributes:
                    upload_cloudwatch_log("No Vehicle attributes", awsConfig, envConfig)
                    return False

                if vehicle_attributes:
                    vehicle_id = vehicle_attributes.get("VID")
                    vehicle_class = vehicle_attributes.get("class")

                # veh mode
                priority = vehicle_attributes.get("priority")
                if priority == "High":
                    vehicle_mode = 0
                else:
                    vehicle_mode = 1

                # use communicator data to get agency data
                url = f"{envConfig.cdf_url}/groups/%2F{region}%2F{agency}"

                code = send_request(
                    url,
                    "GET",
                    region_name=awsConfig["aws_region"],
                    headers=awsConfig["headers"],
                )  # noqa: E501

                if not code:
                    upload_cloudwatch_log("No agency_data", awsConfig, envConfig)
                    return False

                agency_data = json.loads(code)
                agency_attributes = agency_data.get("attributes")
                if not agency_attributes:
                    upload_cloudwatch_log("No agency attributes", awsConfig, envConfig)
                    return False

                vehicle_city_id = agency_attributes.get("agencyCode")
                if not vehicle_city_id:
                    upload_cloudwatch_log("No vehicle_city_id", awsConfig, envConfig)
                    return False

                agency_id = agency_attributes.get("agencyID")
                if not agency_id:
                    upload_cloudwatch_log("No agency_id", awsConfig, envConfig)
                    return False

                cms_id = agency_attributes.get("CMSId")
                if not cms_id:
                    upload_cloudwatch_log("No cms_id", awsConfig, envConfig)
                    return False

                envConfig.device_dict[client_id.lower()] = {
                    "ID": client_id,
                    "vehicleID": vehicle_id,
                    "vehicleClass": vehicle_class,
                    "vehicleCityID": vehicle_city_id,
                    "agencyID": agency_id,
                    "GTTSerial": gtt_serial,
                    "CMSID": cms_id,
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
                client_id, str(e)
            ),
            awsConfig,
            envConfig,
        )
        return False
    return False


def retrieve_large_data(data, awsConfig, envConfig):
    """Get all information from the incoming data, append CDF information for each message and convert each message in form of a RT_Message.
    We simply access each value through its column-name.

    Args:
        data (List of PySpark's Row): incoming data in form of pyspark's row.

    Returns:
        tuple: of RT_message which contains various fields to convey information about the message.
    """
    pub_topic = data["topic"]
    # ! iot_timestamp is not being provided by IoT TopicRules to KinesisDeliveryStream
    iot_timestamp = (
        # handle data format from pilot
        data["utcTime"]
        if "utcTime" in data
        else data["timestamp"]
        if "timestamp" in data
        else "No_iot_timestamp"
    )
    # Decode message back to bytes
    message = base64.standard_b64decode(
        # handle data format from pilot
        data["buffer"]
        if "buffer" in data
        else data["data"]
    )

    # Pull out client_id which is 2100EE0006 in Topic below
    # Example Topic for 2100 - EVP: GTT/GTT/VEH/EVP/2100/2100EE0006/RTRADIO
    # Example Topic for 2101 - TSP: GTT/GTT/VEH/EVP/2101/{Device ID}/RTRADIO
    split_topic = pub_topic.split("/")
    client_id = split_topic[5]

    # Create a dict of one message that will contain all information related to the message.
    # By default it will contain information from incoming_message.
    # We will append additional information from CDF as well.
    message_details = {
        "message": message,
        "pub_topic": pub_topic,
        "iot_timestamp": iot_timestamp,
        "client_id": client_id,
    }

    # a default RT_Message, will get updated later.
    rt_message = (
        "No related Device found in CDF",
        "Error",
        1,
        1,
        0.001,
        0.001,
        1,
        0.0,
        1,
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
        "Error",
        iot_timestamp,
        "Error",
    )  # noqa: E501

    if client_id.lower() in envConfig.device_dict:
        # Use from cache if already there.
        # Append the additional CDF fields to the message details.
        message_details = append_cdf_info(
            message_details, client_id, awsConfig, envConfig
        )
        rt_message = create_message(message_details)
    else:
        # Get details from CDF and append those fields to message details.
        success = get_details_from_cdf(client_id, awsConfig, envConfig)
        if success:
            message_details = append_cdf_info(
                message_details, client_id, awsConfig, envConfig
            )
            rt_message = create_message(message_details)
        else:
            upload_cloudwatch_log(
                "Error in getting details from CDF for client: " + client_id,
                awsConfig,
                envConfig,
            )
    return rt_message


def process_data(sparkSqlConfig, awsConfig, envConfig) -> DataFrame:
    """Convert all the messages received in a consistent format.

    Returns:
        DataFrame: of processed messages.
    """

    # 1. Get the processed dataframe from S3
    # 2. Use each Row to create an Individual DataFrame and adds value of each message.
    # 3. Create a schema and align each message in this particular schema.
    # 4. Create a DataFrame of the processed messages.
    df = fetch_s3data(sparkSqlConfig, awsConfig, envConfig)

    # feed the initial_data into the retrieve method
    large_df = df.rdd.flatMap(lambda x: (retrieve_large_data(x, awsConfig, envConfig),))

    schema = StructType(  # noqa: F405
        [
            StructField("CMSId", StringType(), True),  # noqa: F405, E501
            StructField("GTTSerial", StringType(), True),  # noqa: F405, E501
            StructField("UnitId", IntegerType(), True),  # noqa: F405, E501
            StructField("rssi", IntegerType(), True),  # noqa: F405, E501
            StructField("Latitude", DoubleType(), True),  # noqa: F405, E501
            StructField("Longitude", DoubleType(), True),  # noqa: F405, E501
            StructField("Heading", IntegerType(), True),  # noqa: F405, E501
            StructField("Speed", DoubleType(), True),  # noqa: F405, E501
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
    return_df = sparkSqlConfig["sqlContext"].createDataFrame(large_df, schema)

    return return_df
