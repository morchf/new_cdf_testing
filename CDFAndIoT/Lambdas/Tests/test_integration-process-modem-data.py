import pytest
import os
import sys

# allow tests to find all the code they needs to run
sys.path.append(
    os.path.join(
        os.path.abspath(os.path.realpath(__file__) + 2 * "/.."),
        "ProcessModemData",
        "lambda-code",
    )
)

pmd = __import__("ProcessModemData")


def test_all_data_msg(setup_teardown_CDF_vehicle, mock_event):
    # CDF sends nothing back on successful PATCH
    assert pmd.lambda_handler(mock_event, None) == b""


def test_no_data_msg(setup_teardown_CDF_vehicle, mock_event):
    with pytest.raises(Exception) as info:
        mock_event["1576175734002"] = ""
        pmd.lambda_handler(mock_event, None)
    assert str(info.value) == "No data in event"


def test_no_topic_msg(setup_teardown_CDF_vehicle, mock_event):
    with pytest.raises(Exception) as info:
        del mock_event["topic"]
        pmd.lambda_handler(mock_event, None)
    assert str(info.value) == "No topic in event"


def test_timestamp_no_data_msg(setup_teardown_CDF_vehicle, mock_event):
    for key in mock_event["1576175734002"]:
        del key
    assert pmd.lambda_handler(mock_event, None) == b""


def test_GPIO_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["auxiliaryIo"] = 10
    assert pmd.lambda_handler(mock_event, None) == b""


def test_lat_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["lat"] = 44.098
    assert pmd.lambda_handler(mock_event, None) == b""


def test_long_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["long"] = 0.1010
    assert pmd.lambda_handler(mock_event, None) == b""


def test_fixStatus_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["fixStatus"] = "1"
    assert pmd.lambda_handler(mock_event, None) == b""


def test_satellite_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["numFixSat"] = 14
    assert pmd.lambda_handler(mock_event, None) == b""


def test_heading_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["heading"] = 55
    assert pmd.lambda_handler(mock_event, None) == b""


def test_speed_msg(setup_teardown_CDF_vehicle, mock_event):
    mock_event["speed"] = 55
    assert pmd.lambda_handler(mock_event, None) == b""
