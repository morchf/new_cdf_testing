#######################################
# Helper methods to process 2100 Data #
#######################################


import math
from decimal import Decimal

__all__ = [
    "display_longitude_from_raw",
    "display_latitude_from_raw",
    "decode_speed",
    "decode_heading",
    "decode_op_turn_status",
]


def display_longitude_from_raw(raw):
    MINLONGITUDE = -180
    MAXLONGITUDE = 180
    if raw == -360:
        return ""
    dec = Decimal(raw * 0.000001)
    long = dm_to_decimal_degree(float(dec))
    if long > MAXLONGITUDE:
        return "{:.6f}".format(MAXLONGITUDE)
    if long < MINLONGITUDE:
        return "{:.6f}".format(MINLONGITUDE)
    return "{:.6f}".format(long)


def display_latitude_from_raw(raw):
    MINLATITUDE = -90
    MAXLATITUDE = 90
    if raw == -360:
        return ""
    dec = Decimal(raw * 0.000001)
    lat = dm_to_decimal_degree(float(dec))
    if lat > MAXLATITUDE:
        return "{:.6f}".format(MAXLATITUDE)
    if lat < MINLATITUDE:
        return "{:.6f}".format(MINLATITUDE)
    return "{:.6f}".format(lat)


def dm_to_decimal_degree(degree):
    deg = math.trunc(degree)
    # Minutes shift over two decimal places and divide by 60
    MMmm = (abs(degree) - abs(deg)) * 100
    decimalDegree = deg + MMmm / 60

    if deg < 0:
        decimalDegree = deg - MMmm / 60
    elif deg == 0:
        if deg < 0:
            return -(MMmm / 60)
        else:
            return MMmm / 60
    return decimalDegree


def decode_speed(speed):
    int_speed = int.from_bytes(speed, byteorder="little")
    return float((int_speed * 25) / 18)


def decode_heading(heading):
    int_heading = int.from_bytes(heading, byteorder="little")
    return int((int_heading - 0.5) * 2)


def decode_op_turn_status(opturnStatus):
    # getting bits at position 24-27
    VehMode = bin(opturnStatus >> 5 & 0b11)
    OpStatus = bin(opturnStatus >> 2 & 0b11)
    TurnStatus = bin(opturnStatus >> 0 & 0b1)

    return int(VehMode, 2), int(OpStatus, 2), int(TurnStatus, 2)
