import codecs
import json
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import lit
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
    atp_data_processor,
    convert_gpi,
    convert_gps_status,
    convert_heading,
    convert_lat_lon_to_minutes_degrees,
    convert_speed,
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
    # assuming agency code is always available
    # as it is required field in CDF templates
    vehicle_city_id_bytes = int(message_details["vehicleCityID"]).to_bytes(
        1, byteorder="little", signed=False
    )
    # assuming vehicle class is always available
    # as it is required field in CDF templates
    vehicle_class_bytes = int(message_details["vehicleClass"]).to_bytes(
        1, byteorder="little", signed=False
    )

    # assuming vehicle id is always available
    # as it is required field in CDF templates
    vehicle_id_bytes = int(message_details["vehicleID"]).to_bytes(
        2, byteorder="little", signed=False
    )  # noqa: E501

    unit_id_bytes = int(message_details["vehicleSerialNo"]).to_bytes(
        4, byteorder="little", signed=False
    )

    lat = message_details["latitude"]  # Current latitude
    lon = message_details["longitude"]  # Current longitude
    hdg = message_details["direction"]  # Current heading
    spd = message_details["speed"]  # Current speed kmph
    stt = message_details["atp_gstt"]  # GPS fix status (0 = no fix, 1 = fix)
    gpi = message_details["atp_gpi"]  # GPIO state - bit masked

    # process GPS message and create RTRADIO message
    gps_lat_dddmmmmmm, gps_lon_dddmmmmmm = convert_lat_lon_to_minutes_degrees(lat, lon)

    # IO Mapping
    # IO 1 == ignition
    # IO 2 == left blinker
    # IO 3 == right blinker
    # IO 4 == light bar
    # IO 5 == disable
    # use new GPIO data if available

    turn_status, op_status = convert_gpi(gpi)

    # pack up data
    veh_mode_op_turn = turn_status
    veh_mode_op_turn |= op_status << 2
    veh_mode_op_turn |= int(message_details["vehicleMode"]) << 5
    veh_mode_op_turn = veh_mode_op_turn.to_bytes(
        1, byteorder="little", signed=False
    )  # noqa: E501

    velocity_mpsd5 = convert_speed(spd)

    hdg_deg2 = convert_heading(hdg)

    gps_status = convert_gps_status(stt)

    gpsc_stat = gps_status.to_bytes(2, byteorder="little", signed=False)

    # default
    # MP70 does not provide rssi information set to 0
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
        int(turn_status),  # type: ignore
        op_status,
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
                url = f"{envConfig.cdf_url}/devices/{vehicle.lower()}"

                code = send_request(
                    url,
                    "GET",
                    region_name=awsConfig["aws_region"],
                    headers=awsConfig["headers"],
                )  # noqa: E501
                vehicle_data = json.loads(code)
                vehicle_attributes = vehicle_data.get("attributes")
                if not vehicle_attributes:
                    return False

                # use communicator data to get agency data
                url = f"{envConfig.cdf_url}/groups/%2F{region}%2F{agency}"

                code = send_request(
                    url,
                    "GET",
                    region_name=awsConfig["aws_region"],
                    headers=awsConfig["headers"],
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

                envConfig.device_dict[client_id.lower()] = {
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
                client_id, str(e)
            ),
            awsConfig,
            envConfig,
        )
        return False
    return False


def retrieve_large_data(data, awsConfig, envConfig):
    atp_ghed = data["atp_ghed"]
    atp_glat = data["atp_glat"]
    atp_glon = data["atp_glon"]
    atp_gpi = data["atp_gpi"]
    atp_gspd = data["atp_gspd"]
    atp_gstt = data["atp_gstt"]
    device_timestamp = data["device_timestamp"]
    iot_timestamp = data["timestamp"]
    # client_id is the serial number embedded in the topic structure
    #   EVP:  {Serial_Number}/message/json
    #   TSP:  SW/{Serial_Number}/GTT/SIERRA/VEH/TSP/MP70/#
    client_id = data["topic"].split("/")[
        0 if envConfig.device_operational_mode == "EVP" else 1
    ]

    # Create a dict of one message that will contain all information related to the message.

    # By default it will contain information from incoming_message.
    # We will append additional information from CDF as well.
    message_details = {
        "direction": atp_ghed,
        "latitude": atp_glat,
        "longitude": atp_glon,
        "speed": atp_gspd,
        "atp_gstt": atp_gstt,
        "atp_gpi": atp_gpi,
        "device_timestamp": device_timestamp,
        "iot_timestamp": iot_timestamp,
        "client_id": client_id,
    }

    # A default rt_message. Will be changed later.
    rt_message = (
        "No related Device found in CDF",
        "Error",
        1,
        1,
        atp_glat,
        atp_glon,
        atp_ghed,
        atp_gspd,
        atp_gstt,
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
    device_timestamp_s = df.select("data.*").columns
    rdd_list = []
    topic_time_rdd_list = []
    for device_timestamp in device_timestamp_s:
        timestamp_topic_df = df.select(
            f"data.{device_timestamp}", "timestamp", "topic"
        )  # noqa: E501
        temp_df = timestamp_topic_df.withColumn(
            "device_timestamp", lit(device_timestamp)
        )
        temp_df = temp_df.na.drop()
        clean_topic_time_rdd = temp_df.select(
            "timestamp", "topic", "device_timestamp"
        ).rdd
        topic_time_rdd_list.append(clean_topic_time_rdd)
        int_data_df = df.select(f"data.{device_timestamp}.*")
        int_atp_df = atp_data_processor(device_timestamp, int_data_df)
        rdd_list.append(int_atp_df)

    atp_rdd = sparkSqlConfig["sc"].union(rdd_list)
    topic_time_rdd = sparkSqlConfig["sc"].union(topic_time_rdd_list)
    atp_df = atp_rdd.toDF()
    topic_time_df = topic_time_rdd.toDF().drop()

    # check if the data contains atp_gstt,
    # if not create one with zeros
    if not "atp_gstt" in atp_df.columns:  # noqa: E713
        atp_df = atp_df.withColumn("atp_gstt", lit(None))
    initial_data = atp_df.join(
        topic_time_df,
        topic_time_df.device_timestamp == atp_df.device_timestamp,
        "inner",
    ).drop(topic_time_df.device_timestamp)
    # feed the initial_data into the retrieve method
    large_df = initial_data.rdd.flatMap(
        lambda x: (retrieve_large_data(x, awsConfig, envConfig),)
    )

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
