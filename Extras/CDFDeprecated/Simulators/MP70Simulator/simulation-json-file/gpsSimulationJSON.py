import math
import json
import time


def __get_bearing(lat1, lon1, lat2, lon2):
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


def __get_great_circle_distance(lat1, lon1, lat2, lon2):
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


def __calculate_intermediate_point(lat1, lon1, lat2, lon2, fraction):
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


# takes in list of lists, where each individual list takes the format:
# [begin lat, begin lon, end lat, end lon, mph, gpio]
# time is also customizable and must be entered in format of seconds
# after epoch if no time is entered, the current time will be used
# instead returns json logs in list of strings with each entry being
# one log
def get_json_messages(input_list, time_int=int(time.time())):
    logs_list = []
    # preliminary calculation
    for (
        original_lat,
        original_long,
        ending_lat,
        ending_long,
        mph_int,
        gpi_int,
    ) in input_list:
        meters_per_second = 0.44704 * mph_int
        true_path = __get_bearing(original_lat, original_long, ending_lat, ending_long)
        per_second_fraction = meters_per_second / __get_great_circle_distance(
            original_lat, original_long, ending_lat, ending_long
        )
        fraction_of_path_consumed = 0

        while fraction_of_path_consumed < 1:
            new_point = __calculate_intermediate_point(
                original_lat,
                original_long,
                ending_lat,
                ending_long,
                fraction_of_path_consumed,
            )
            fraction_of_path_consumed += per_second_fraction
            outer_dict = {
                time_int: {
                    "atp.glat": new_point[0],
                    "atp.glon": new_point[1],
                    "atp.gspd": mph_int,
                    "atp.ghed": true_path,
                    "atp.gpi": gpi_int,
                }
            }
            logs_list.append(json.dumps(outer_dict, indent=3))
            time_int += 1
    return logs_list


# write list of inputted logs to txt files
def logs_to_file(list_of_logs):
    file_count = 0
    for single_log in list_of_logs:
        file_name = "log" + str(file_count) + ".txt"
        text_file = open(file_name, "wt")
        text_file.write(single_log)
        text_file.close()
        file_count += 1


# EXAMPLE CALLS:


# input fields          begin lat   begin lon    end lat   end lon  speed gpio
lat_long_speed_list = [
    [44.898042, -93.105859, 44.898026, -93.095929, 60, 7],
    [44.898026, -93.095929, 44.898042, -93.105859, 40, 9],
]

# the above call would simulate a vehicle going from point a
# to point b at 60 mph, then from point b to point a at 40 mp

# time = 1602710737
# all_logs = get_json_messages(lat_long_speed_list,time)

# retrieves list of json logs (check comment above function)
all_logs = get_json_messages(lat_long_speed_list)

# writes inputted list of logs to txt files with individual logs
# (check comment above function)
logs_to_file(all_logs)
