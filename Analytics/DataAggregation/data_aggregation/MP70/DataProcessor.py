from pyspark.sql.functions import lit

__all__ = [
    "convert_lat_lon_to_minutes_degrees",
    "to_min_degrees",
    "convert_speed",
    "convert_heading",
    "atp_data_processor",
    "convert_gps_status",
    "convert_gpi",
]


#######################################
# Helper methods to process MP70 Data #
#######################################


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
    Speed coming is in km/h, needs to be converted to
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
    """Heading/Direction is coming in degrees, needs to be converted to format of heading per two degrees.

    Args:
        heading (_type_): heading/direction data received from incoming data.

    Returns:
        bytes: heading/direction data in bytes, to be used in rt_message.
    """
    if heading is None:
        heading = 0
    new_heading = int(heading / 2 + 0.5)
    return new_heading.to_bytes(1, byteorder="little", signed=False)


def atp_data_processor(device_timestamp, data_df):
    transformed_data = data_df.toDF(
        *(c.replace(".", "_") for c in data_df.columns)
    )  # noqa: E501
    transformed_data = transformed_data.withColumn(
        "device_timestamp", lit(device_timestamp)
    )

    return transformed_data.na.drop().rdd


def convert_gps_status(stt):
    gps_status = 0
    if stt == 0:
        gps_status &= 0x3FFF
    else:
        gps_status |= 0xC000
    return int(gps_status)


def convert_gpi(gpi):
    if gpi is not None:
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

        op_status = 0
        # op status
        if not ignition or disable:
            op_status = 0
        elif light_bar and ignition and not disable:
            op_status = 1

        return turn_status, op_status
    return None, None
