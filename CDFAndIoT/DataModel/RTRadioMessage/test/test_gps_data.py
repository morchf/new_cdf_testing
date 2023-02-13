import random

from gtt.data_model.rt_radio_message import GPSData


# 'source of truth' pulled from TSP CreateRTRadioMessage lambda
def to_min_degrees(data):
    data = float(data)
    ddd = int(data)
    mmmmmm = float(data - float(ddd)) * 60
    data = (ddd * 1000000 + int(mmmmmm * 10000)) / 1000000
    new_string = hex(int(data * 1000000))
    int_data = int(new_string, 16)
    return int_data


def test_min_degrees():
    # Test with both positive
    for i in range(10):
        latitude = random.uniform(0, 90)
        longitude = random.uniform(0, 180)
        _test_min_degrees(latitude, longitude)

    # Test with negative latitude
    for i in range(10):
        latitude = random.uniform(-90, 0)
        longitude = random.uniform(0, 180)
        _test_min_degrees(latitude, longitude)

    # Test with negative longitude
    for i in range(10):
        latitude = random.uniform(0, 90)
        longitude = random.uniform(-180, 0)
        _test_min_degrees(latitude, longitude)

    # Test with both negative
    for i in range(10):
        latitude = random.uniform(-90, 0)
        longitude = random.uniform(-180, 0)
        _test_min_degrees(latitude, longitude)


def _test_min_degrees(latitude, longitude):
    expected_min_lat = to_min_degrees(latitude)
    expected_min_lon = to_min_degrees(longitude)
    actual_min_lat, actual_min_lon = GPSData(
        latitude=latitude, longitude=longitude, speed=0, heading=0
    ).minute_degrees()

    # Slightly different rounding is tolerated to within one ten-thousandth of a minute degree
    assert within_one(expected_min_lat, actual_min_lat)
    assert within_one(expected_min_lon, actual_min_lon)


def within_one(a, b):
    return a <= (b + 1) and a >= (b - 1)
