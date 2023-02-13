import math


def get_time_int(seconds_after_zero):
    hours = int(seconds_after_zero / 3600)
    minutes = int((seconds_after_zero % 3600) / 60)
    seconds = seconds_after_zero % 60
    final_time = (hours * 10000) + (minutes * 100) + seconds
    return final_time


def checksum(sentence):
    # Sentence Structure: $GPRMC,155214.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A
    sentence = sentence.strip()

    calc_cksum = 0
    for s in sentence:
        calc_cksum ^= ord(s)

    return hex(calc_cksum)


def to_degrees_minutes(decimal_degrees):
    string = "4457.1415,N,09256.7108,W"
    latitude_direction = "N"
    longitude_direction = "E"
    lat_decimal = decimal_degrees[0]
    lon_decimal = decimal_degrees[1]
    lat_degrees = int(lat_decimal)
    lon_degrees = int(lon_decimal)
    lat_minutes = (lat_decimal - lat_degrees) * 60
    lon_minutes = (lon_decimal - lon_degrees) * 60
    final_lat_number = (lat_degrees * 100) + lat_minutes
    final_lon_number = (lon_degrees * 100) + lon_minutes
    if final_lat_number < 0:
        latitude_direction = "S"
    if final_lon_number < 0:
        longitude_direction = "W"
    final_lat_number = abs(final_lat_number)
    final_lon_number = abs(final_lon_number)
    lon_string = "{:.4f}".format(final_lon_number)
    if float(lon_string) < 10000:
        lon_string = "0" + lon_string
    string = (
        "{:.4f}".format(final_lat_number)
        + ","
        + latitude_direction
        + ","
        + lon_string
        + ","
        + longitude_direction
    )
    return string


def get_bearing(lat1, lon1, lat2, lon2):
    lat1_radians = math.radians(lat1)
    lat2_radians = math.radians(lat2)
    lon1_radians = math.radians(lon1)
    lon2_radians = math.radians(lon2)
    y = math.sin(lon2_radians - lon1_radians) * math.cos(lat2_radians)
    x = math.cos(lat1_radians) * math.sin(lat2_radians) - math.sin(
        lat1_radians
    ) * math.cos(lat2_radians) * math.cos(lon2_radians - lon1_radians)
    theta = math.atan2(y, x)
    bearing = (math.degrees(theta) + 360) % 360
    return bearing


def get_great_circle_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371000
    lat1_radians = math.radians(lat1)
    lat2_radians = math.radians(lat2)
    lon1_radians = math.radians(lon1)
    lon2_radians = math.radians(lon2)
    diff_lat = lat2_radians - lat1_radians
    diff_lon = lon2_radians - lon1_radians
    a = (math.sin(diff_lat / 2) * math.sin(diff_lat / 2)) + (
        math.cos(lat1_radians)
        * math.cos(lat2_radians)
        * math.sin(diff_lon / 2)
        * math.sin(diff_lon / 2)
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = earth_radius * c
    return d


def calculate_intermediate_point(lat1, lon1, lat2, lon2, fraction):
    lat1_radians = math.radians(lat1)
    lat2_radians = math.radians(lat2)
    lon1_radians = math.radians(lon1)
    lon2_radians = math.radians(lon2)
    diff_lat = lat2_radians - lat1_radians
    diff_lon = lon2_radians - lon1_radians
    a = (math.sin(diff_lat / 2) * math.sin(diff_lat / 2)) + (
        math.cos(lat1_radians)
        * math.cos(lat2_radians)
        * math.sin(diff_lon / 2)
        * math.sin(diff_lon / 2)
    )
    delta = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    capital_a = math.sin((1 - fraction) * delta) / math.sin(delta)
    capital_b = math.sin(fraction * delta) / math.sin(delta)
    x = (capital_a * math.cos(lon1_radians) * math.cos(lat1_radians)) + (
        capital_b * math.cos(lat2_radians) * math.cos(lon2_radians)
    )
    y = (capital_a * math.cos(lat1_radians) * math.sin(lon1_radians)) + (
        capital_b * math.cos(lat2_radians) * math.sin(lon2_radians)
    )
    z = (capital_a * math.sin(lat1_radians)) + (capital_b * math.sin(lat2_radians))
    intermediate_lat_radians = math.atan2(z, math.sqrt((x * x) + (y * y)))
    intermediate_lon_radians = math.atan2(y, x)
    intermediate_lat = math.degrees(intermediate_lat_radians)
    intermediate_lon = math.degrees(intermediate_lon_radians)
    returned_list = [intermediate_lat, intermediate_lon]
    return returned_list


def get_gprmc_messages(
    original_lat,
    original_long,
    ending_lat,
    ending_long,
    mph_int,
    date_string,
    time_string,
):
    logs_list = []
    # preliminary calculation
    meters_per_second = 0.44704 * mph_int

    knots = mph_int * 0.868976
    true_path = get_bearing(original_lat, original_long, ending_lat, ending_long)
    per_second_fraction = meters_per_second / get_great_circle_distance(
        original_lat, original_long, ending_lat, ending_long
    )
    fraction_of_path_consumed = 0
    hours_min_seconds = time_string.split(":")
    time_in_seconds = (
        (int(hours_min_seconds[0]) * 3600)
        + (int(hours_min_seconds[1]) * 60)
        + (int(hours_min_seconds[2]))
    )
    stripped_date_string = date_string.replace("/", "")

    while fraction_of_path_consumed < 1:
        new_point = calculate_intermediate_point(
            original_lat,
            original_long,
            ending_lat,
            ending_long,
            fraction_of_path_consumed,
        )
        location_string = to_degrees_minutes(new_point)
        fraction_of_path_consumed += per_second_fraction
        log = (
            "$GPRMC,"
            + "{:.3f}".format(get_time_int(time_in_seconds))
            + ",A,"
            + location_string
            + ","
            + "{:.2f}".format(knots)
            + ","
            + "{:.2f}".format(true_path)
            + ","
            + stripped_date_string
            + ",,,A"
        )
        check_sum = checksum(log)
        final_log = log + "*" + (str(check_sum)[2:4]).upper()
        logs_list.append(final_log)
        time_in_seconds += 1
    return logs_list
