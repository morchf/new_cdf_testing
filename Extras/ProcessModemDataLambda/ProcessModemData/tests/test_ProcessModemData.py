import pytest
import json
import os
import sys
from unittest.mock import patch

# allow tests to find all the code they needs to run
sys.path.append("../lambda-code")
os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"
os.environ["AWS_REGION"] = "us-east-1"

import ProcessModemData as pmd


@pytest.fixture()
def mock_data():
    comm_data = open_json_file("valid_comm_cdf_data.json")
    data = [comm_data, ""]
    return data


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
    else:
        print(f"{file_name} not found.")
    return json_str


def test_all_data_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {
                "atp.glat": 44.9512963,
                "atp.ghed": 19,
                "atp.glon": -92.9453703,
                "atp.gspd": 5,
                "atp.gpi": 4,
                "atp.gstt": 1,
                "atp.gsat": 3,
                "atp.gqal": 1,
            },
            "topic": "unitTestModem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
        params='{"attributes":{"fixStatus":1,"numFixSat":3,"lat":44.9512963,"long":-92.9453703,"heading":19,"speed":5,"auxiliaryIo":4,"lastGPIOMsgTimestamp":"1576175734002","lastGPSMsgTimestamp":"1576175734002"}}',
    )


def test_no_data_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        with pytest.raises(Exception):
            mock.side_effect = mock_data
            event = {"topic": "unit-test-modem/messages/json"}

            pmd.lambda_handler(event, None)

    mock.assert_called_once()


def test_no_topic_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        with pytest.raises(Exception):
            mock.side_effect = mock_data
            event = {
                "1576175734002": {
                    "atp.glat": 44.9512963,
                    "atp.ghed": 19,
                    "atp.glon": -92.9453703,
                    "atp.gspd": 5,
                    "atp.gpi": 4,
                    "atp.gstt": 1,
                    "atp.gsat": 3,
                    "atp.gqal": 1,
                }
            }

            pmd.lambda_handler(event, None)

    mock.assert_not_called()


def test_timestamp_no_data_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        with pytest.raises(Exception):
            mock.side_effect = mock_data
            event = {"1576175734002": {}, "topic": "unit-test-modem/messages/json"}

            pmd.lambda_handler(event, None)

    mock.assert_not_called()


def test_no_associated_vehicle(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        with pytest.raises(Exception) as info:

            json_obj = json.loads(mock_data[0])
            del json_obj["devices"]
            mock_data[0] = json.dumps(json_obj)
            mock.side_effect = mock_data

            print(mock_data)
            event = {
                "1576175734002": {
                    "atp.glat": 44.9512963,
                    "atp.ghed": 19,
                    "atp.glon": -92.9453703,
                    "atp.gspd": 5,
                    "atp.gpi": 4,
                    "atp.gstt": 1,
                    "atp.gsat": 3,
                    "atp.gqal": 1,
                },
                "topic": "unitTestModem/messages/json",
            }

            pmd.lambda_handler(event, None)
    assert str(info.value) == "No vehicle associated with communicator"
    mock.assert_called_once()


def test_no_associated_vehicle_installedat(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        with pytest.raises(Exception) as info:

            json_obj = json.loads(mock_data[0])
            del json_obj["devices"]["installedat"]
            mock_data[0] = json.dumps(json_obj)

            mock.side_effect = mock_data

            print(mock_data)
            event = {
                "1576175734002": {
                    "atp.glat": 44.9512963,
                    "atp.ghed": 19,
                    "atp.glon": -92.9453703,
                    "atp.gspd": 5,
                    "atp.gpi": 4,
                    "atp.gstt": 1,
                    "atp.gsat": 3,
                    "atp.gqal": 1,
                },
                "topic": "unitTestModem/messages/json",
            }

            pmd.lambda_handler(event, None)
    assert str(info.value) == "No vehicle associated with communicator"
    mock.assert_called_once()


def test_GPIO_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.gpi": 4},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"auxiliaryIo":4,"lastGPIOMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )


def test_lat_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.glat": 44.9512963},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"lat":44.9512963,"lastGPSMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )


def test_long_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.glon": -92.9453703},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"long":-92.9453703,"lastGPSMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )


def test_fixStatus_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.gstt": 1},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"fixStatus":1,"lastGPSMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )


def test_satellite_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.gsat": 3},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"numFixSat":3,"lastGPSMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )


def test_heading_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.ghed": 19},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"heading":19,"lastGPSMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )


def test_speed_msg(mock_data):
    with patch("ProcessModemData.sendRequest") as mock:
        mock.side_effect = mock_data
        event = {
            "1576175734002": {"atp.gspd": 5},
            "topic": "unit-test-modem/messages/json",
        }

        pmd.lambda_handler(event, None)

    mock.assert_called_with(
        "mock_url/devices/unittestveh",
        "PATCH",
        "us-east-1",
        params='{"attributes":{"speed":5,"lastGPSMsgTimestamp":"1576175734002"}}',
        headers={
            "Accept": "application/vnd.aws-cdf-v2.0+json",
            "Content-Type": "application/vnd.aws-cdf-v2.0+json",
        },
    )
