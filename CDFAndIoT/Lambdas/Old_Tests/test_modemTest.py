"""
glitch: time difference between 2 consecutive messages in seconds
max_glitch: max time difference for each vehicle
mean_glitch: mean time difference for each vehicle
mean_glitch: how many glitches greater than 1 for each vehicle

pct_miss: total seconds missed. EX: received in total 1600 instead of \
    1800 messages in 30 minutes then pct_miss = 200/1800 = 11.11%

mean_trans_time: mean time difference between iot core received and modem message sent
"""
from modemTest import modem_test

# Config
vehicle_serialNum = ["SimDevice0101", "SimDevice0102"]
listen_time = 1
region_name = "us-east-1"


def test_modem_test():
    prescreen, postscreen = modem_test(
        vehicle_serialNum, listen_time, region_name)

    # prescreen test for topic and message content
    assert prescreen is True, postscreen

    # Among all vehicles, test if all max glitch <= 20
    max_glitch_in_range = postscreen["max_glitch"].le(20)
    max_glitch_in_range = max_glitch_in_range.eq(True).all()
    assert max_glitch_in_range, ">= 1 vehicle has max glitch greater than 20 seconds"

    # Among all vehicles, test if all mean glitch <= 3
    mean_glitch_in_range = postscreen["mean_glitch"].le(3)
    assert mean_glitch_in_range.eq(
        True
    ).all(), ">= 1 vehicle has mean_glitch greater than 3 seconds"

    # Among all vehicles, test if all pct_miss <= 40%
    pct_miss_in_range = postscreen["pct_miss"].le(0.4)
    assert pct_miss_in_range.eq(
        True
    ).all(), ">= 1 vehicle has pct_miss greater than 40%"

    # Among all vehicles, test if all mean_trans_time is between 0 and 1
    mean_trans_time_in_range = postscreen["mean_trans_time"].between(0, 1)
    assert mean_trans_time_in_range.eq(
        True
    ).all(), ">= 1 vehicle has mean_trans_time not in [0, 1]"
