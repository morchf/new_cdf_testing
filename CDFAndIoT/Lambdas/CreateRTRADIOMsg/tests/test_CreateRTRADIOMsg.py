import pytest
import json
import os
import sys
from unittest.mock import patch

# allow tests to find all the code they needs to run
sys.path.append("../lambda-code")

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "mock_url"

import CreateRTRADIOMsg as crm


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


def test_to_min_degrees_valid_string_value():
    assert crm.to_min_degrees("12.87") == b"\x0f\x12\xbf\x00"


def test_to_min_degrees_valid_int_value():
    assert crm.to_min_degrees(12) == b"\x00\x1b\xb7\x00"


def test_to_min_degrees_valid_float_value():
    assert crm.to_min_degrees(12.87) == b"\x0f\x12\xbf\x00"


def test_convert_lat_long_to_minutes_degrees_int():
    assert crm.convert_lat_lon_to_minutes_degrees(20, 40) == (
        b"\x00-1\x01",
        b"\x00Zb\x02",
    )


def test_convert_speed_int():
    assert crm.convert_speed(15) == b"\x14"


def test_convert_heading_int():
    assert crm.convert_heading(77) == b"'"


def test_valid_data(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:
                mock_send_request.side_effect = cdf_mock_data

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

                mock_iot.assert_called_with(
                    "Publish",
                    {
                        "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
                        "qos": 0,
                        "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
                    },
                )


def test_no_topic(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:

            mock_send_request.side_effect = cdf_mock_data

            event = open_json_file("valid_data.json")
            event = json.loads(event)
            del event["topic"]

            crm.lambda_handler(event, None)
    # if exception expected asserts must be checked outside the context manager(s)
    assert str(info.value) == "No topic in event data"


def test_no_template_id_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["templateId"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No template id in device CDF data"
    )


def test_no_groups_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["groups"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No groups in communicator CDF data"
    )


def test_no_groups_ownedby_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["groups"]["ownedby"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No groups in communicator CDF data"
    )


def test_no_attributes_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["attributes"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No attributes value in communicator CDF data"
    )


def test_no_gttserial_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["attributes"]["gttSerial"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No gtt_serial value in attributes"
    )


def test_no_mac_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["attributes"]["addressMAC"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No MAC address value in attributes"
    )


def test_no_attributes_in_vehicle(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[1])
                del json_obj["attributes"]
                cdf_mock_data[1] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No attributes value in vehicle CDF data"
    )


def test_no_devices_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["devices"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No associated vehicle in communicator CDF data"
    )


def test_no_devices_installedat_in_communicator(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[0])
                del json_obj["devices"]["installedat"]
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                assert crm.lambda_handler(event, None)

    assert (
        str(info.value)
        == "Serial No. is unitTestModem No associated vehicle in communicator CDF data"
    )


def test_no_attributes_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:
                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is unitTestModem No attributes value in Agency json string"
    )


def test_no_agencycode_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["agencyCode"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)
    assert str(info.value) == "Serial No. is unitTestModem Agency Code not found in CDF"


def test_no_agencyid_in_agency(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["agencyID"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is unitTestModem Agency ID (GUID) not found in CDF"
    )


def test_no_cmsguid(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[2])
                del json_obj["attributes"]["CMSId"]
                cdf_mock_data[2] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is unitTestModem Agency Id is F9843B40-464A-4747-A428-A41DF950948E CMS ID (GUID) not found in CDF"
    )


def test_ignition(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x01
                cdf_mock_data[0] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_left_turn(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x02
                cdf_mock_data[0] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_right_turn(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x04
                cdf_mock_data[0] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_lightbar(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x08
                cdf_mock_data[0] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_high_priority(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["priority"] = "High"
                cdf_mock_data[0] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_low_priority(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[1])
                json_obj["attributes"]["priority"] = "Low"
                cdf_mock_data[1] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_op_status(cdf_mock_data):
    with patch("botocore.client.BaseClient._make_api_call") as mock_iot:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache") as mock_cache:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["attributes"]["auxiliaryIo"] = 0x09
                cdf_mock_data[0] = json.dumps(json_obj)

                gtt_serial = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "GTTSerial"
                ]
                cms_id_lower = mock_cache.get_item(Key={"ID": "unittestmodem"})["Item"][
                    "CMSID"
                ].lower()

                mock_send_request.side_effect = cdf_mock_data

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)

    mock_iot.assert_called_with(
        "Publish",
        {
            "topic": f"GTT/{cms_id_lower}/SVR/EVP/2100/{gtt_serial}/RTRADIO/44.95L,-92.94H",
            "qos": 0,
            "payload": b"\x01\x00\x00\x00\x00\x00\x00\x00\x99\x18\xa8\x02J\x89{\xfa\x00\x00\x00\xc0\x00\x00\x00\x00\x01\x00\x01$\x01\x00\x00\x00\x00\x00\x00\x00",
        },
    )


def test_no_class_in_vehicle(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[1])
                del json_obj["attributes"]["class"]
                cdf_mock_data[1] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is unitTestModem Agency Id is F9843B40-464A-4747-A428-A41DF950948E CMS Id is F9843B40-464A-4747-A428-A41DF950948E No class in device attributes"
    )


def test_cei_vehicle(cdf_mock_data):
    with pytest.raises(Exception) as info:
        with patch("CreateRTRADIOMsg.send_request") as mock_send_request:
            with patch("CreateRTRADIOMsg.cache.get_item") as mock_cache_data:

                json_obj = json.loads(cdf_mock_data[0])
                json_obj["templateId"] = "ceivehicle"
                cdf_mock_data[0] = json.dumps(json_obj)

                mock_send_request.side_effect = cdf_mock_data
                mock_cache_data.return_value = {}

                event = open_json_file("valid_data.json")
                event = json.loads(event)

                crm.lambda_handler(event, None)
    assert (
        str(info.value)
        == "Serial No. is unitTestModem communicator does not have templateId; exiting "
    )
