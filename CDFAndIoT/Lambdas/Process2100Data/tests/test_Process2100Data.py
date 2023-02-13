import json
import os
import sys
import time
from unittest.mock import patch

import pytest

# allow tests to find all the code they needs to run
sys.path.append("../lambda-code")

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "mock_url"

import Process2100Data as data2100  # noqa: E402


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
    else:
        print(f"{file_name} not found.")
    return json_str


@pytest.fixture(scope="function")
def cdf_mock_data():
    comm_data = open_json_file("valid_comm_cdf_data.json")
    device_data = open_json_file("valid_vehicle_cdf_data.json")
    agy_data = open_json_file("valid_agency_cdf_data.json")
    reg_data = open_json_file("valid_region_cdf_data.json")
    data = [comm_data, device_data, agy_data, reg_data]
    return data


def test_valid_data(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_sendRequest:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                mock_sendRequest.side_effect = cdf_mock_data

                mock_cache_data.return_value = {
                    "Item": {
                        "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                        "vehicleID": 3326,
                        "vehicleClass": 10,
                        "vehicleCityID": 100,
                        "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                        "ID": "2100NFT37",
                    }
                }

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)

                mock_iot.assert_called_with(
                    "Publish",
                    {
                        "topic": "GTT/888a475f-6504-4aa3-846f-bfebee81dd7b/SVR/EVP/2100/2100NFT37/RTRADIO/90.00L,180.00L",
                        "qos": 0,
                        "payload": b"0\\x02\\x88\\x00\\x00\\xfe\\x0\xfe\x0cd0\n\\x99\\x18\\xa8\\x02J\\x89{\\xfadX\\x00\\xc0\\x00\\x00\\x00\\x00\\xfe\\x0cd\\x04\\n\\x00\\x00\\x00\\x00\\x00\\x00\\x00",  # noqa: E501
                    },
                )


def test_no_topic(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:

            mock_send_request.side_effect = cdf_mock_data

            event = open_json_file("valid_data.json")
            event = json.loads(event)
            del event["topic"]

            data2100.lambda_handler(event, None)
    # if exception expected asserts must be checked outside the context manager(s)
    assert str(info.value) == "No topic in event data"


def test_no_template_id_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["templateId"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)

    assert (
        str(info.value) == "Serial No. is 2100NFT37 No template Id in device CDF data "
    )


def test_no_groups_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["groups"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)

    assert str(info.value) == "Serial No. is 2100NFT37 No groups in CDF data "


def test_no_groups_ownedby_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["groups"]["ownedby"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert data2100.lambda_handler(event, None)

    assert str(info.value) == "Serial No. is 2100NFT37 No groups in CDF data "


def test_no_devices_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["devices"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert data2100.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is 2100NFT37 No associated vehicle in communicator CDF data "
    )


def test_no_attributes_in_vehicle(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[1])
                del json_obj["attributes"]
                cdf_mock_data[1] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert data2100.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is 2100NFT37 No attributes value in vehicle CDF data "
    )


def test_no_attributes_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
    assert (
        str(info.value) == "Serial No. is 2100NFT37 attributes not found in CDF Agency "
    )


def test_no_agencycode_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["agencyCode"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is 2100NFT37 Agency Code not found in CDF Agency "
    )


def test_no_agencyid_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_sendRequest:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["agencyID"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_sendRequest.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is 2100NFT37 Agency ID (GUID) not found in CDF Agency "
    )


def test_no_cmsid_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_sendRequest:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["CMSId"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_sendRequest.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is 2100NFT37 CMS ID (GUID) not found in CDF Agency "
    )


def test_ignition(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x01
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_left_turn(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x02
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_right_turn(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x04
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_lightbar(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x08
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_high_priority(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["priority"] = "High"
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_low_priority(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[1])
                json_obj["attributes"]["priority"] = "Low"
                cdf_mock_data[1] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_op_status(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x09
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
                expiration_time = int(time.time())

    mock_iot.assert_called_with(
        "PutItem",
        {
            "TableName": "CachingTable",
            "Item": {
                "ID": "2100nft37",
                "vehicleID": 3326,
                "vehicleClass": 10,
                "vehicleCityID": 100,
                "agencyID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "CMSID": "888A475F-6504-4AA3-846F-BFEBEE81DD7B",
                "ExpirationTime": expiration_time + 1200,
            },
        },
    )


def test_cei_vehicle(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("Process2100Data.send_request") as mock_send_request:
            with patch("Process2100Data.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["templateId"] = "ceivehicle"
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                data2100.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is 2100NFT37 template_id != communicator; exiting "
    )
