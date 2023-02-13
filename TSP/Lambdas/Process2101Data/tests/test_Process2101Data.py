import pytest
import json
import os
import sys
from unittest.mock import patch

# allow tests to find all the code they needs to run
sys.path.append("../LambdaCode")

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "mock_url"

import Process2101Data as data2101  # noqa: E402


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
    else:
        print(f"{file_name} not found.")
    return json_str


@pytest.fixture(scope="module")
def cdf_mock_data():
    comm_data = open_json_file("valid_comm_cdf_data.json")
    device_data = open_json_file("valid_vehicle_cdf_data.json")
    agy_data = open_json_file("valid_agency_cdf_data.json")
    reg_data = open_json_file("valid_region_cdf_data.json")
    data = [comm_data, device_data, agy_data, reg_data]
    return data


def test_valid_data(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2101Data.sendRequest") as mock_sendRequest:
            mock_sendRequest.side_effect = cdf_mock_data

            event = open_json_file("valid_data.json")
            event = json.loads(event)

            data2101.lambda_handler(event, None)

            mock_iot.assert_called_with(
                "Publish",
                {
                    "topic": "GTT/100/VEH/TSP/2101/2101ZS1111/RTRADIO",
                    "qos": 0,
                    "payload": b"0\x02\x88\x00\x00\xfe\x00\x00\x99\x18\xa8\x02J\x89{\xfadX\x00\xc0\x00\x00\x00\x00\xfe\x0cd\x04\n\x00\x00\x00\x00\x00\x00\x00",  # noqa: E501
                },
            )


def test_no_gttserial_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
            with patch("Process2101Data.sendRequest") as mock_sendRequest:

                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["attributes"]["gttSerial"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_sendRequest.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2101.lambda_handler(event, None)

    assert str(info.value) == "No gttSerial value in attributes"
    mock_iot.assert_not_called()


def test_no_agencyid_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
            with patch("Process2101Data.sendRequest") as mock_sendRequest:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["agencyID"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_sendRequest.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2101.lambda_handler(event, None)
    assert str(info.value) == "Agency ID (GUID) not found in CDF"
    mock_iot.assert_not_called()
