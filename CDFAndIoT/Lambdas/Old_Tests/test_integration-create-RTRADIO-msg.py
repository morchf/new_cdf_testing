import pytest
import os
import sys

# allow tests to find all the code they needs to run
sys.path.append(
    os.path.join(
        os.path.abspath(os.path.realpath(__file__) + 2 * "/.."),
        "CreateRTRADIOMsg",
        "lambda-code",
    )
)

crm = __import__("CreateRTRADIOMsg")
os.environ["AWS_REGION"] = "us-east-1"


def test_valid_data(setup_teardown_CDF_vehicle, mock_event):
    resp = crm.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_no_topic(setup_teardown_CDF_vehicle, mock_event):
    with pytest.raises(Exception) as info:
        del mock_event["topic"]
        crm.lambda_handler(mock_event, None)
    assert str(info.value) == "No topic in event data"


def test_malformed_topic(setup_teardown_CDF_vehicle, mock_event):
    mock_event["topic"] = "unit-test-modem/messages/jso"
    resp = crm.lambda_handler(mock_event, None)
    assert resp == ""


def test_ignition(setup_teardown_CDF_vehicle, mock_event):
    mock_event["auxiliaryIo"] = 1  # only ignition on
    resp = crm.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_left_turn(setup_teardown_CDF_vehicle, mock_event):
    mock_event["auxiliaryIo"] = 2  # only left blinker on
    resp = crm.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_right_turn(setup_teardown_CDF_vehicle, mock_event):
    mock_event["auxiliaryIo"] = 4  # only right blinker on
    resp = crm.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_lightbar(setup_teardown_CDF_vehicle, mock_event):
    mock_event["auxiliaryIo"] = 8  # only lightbar on
    resp = crm.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_op_status(setup_teardown_CDF_vehicle, mock_event):
    mock_event["auxiliaryIo"] = 9  # lightbar and ignition and not disable
    resp = crm.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200
