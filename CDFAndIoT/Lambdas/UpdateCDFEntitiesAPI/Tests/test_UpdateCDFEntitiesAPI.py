import json
import os
import sys
from unittest.mock import patch

sys.path.append("../LambdaCode")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

# os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"
os.environ["AWS_REGION"] = "us-east-1"

import UpdateCDFEntitiesAPI  # noqa: E402

ok = "Ok, have a nice day."


def open_json_file(file_name):
    json_str = None
    json_obj = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
        json_obj = json.loads(json_str)
    else:
        print(f"{file_name} not found.")

    return json_obj


def test_update_region():
    with patch("UpdateCDFEntitiesAPI.update_region") as mock_ui:
        mock_ui.return_value = (True, ok)
        event = open_json_file("region_event.json")
        event["body"] = json.dumps(event["body"])
        message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_reg successfully updated",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_region_failed():
    with patch("UpdateCDFEntitiesAPI.update_region") as mock_ui:
        mock_ui.return_value = (False, "Failed update region")
        event = open_json_file("region_event.json")
        event["body"] = json.dumps(event["body"])
        message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed update region",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_agency():
    with patch("UpdateCDFEntitiesAPI.update_agency") as mock_ui:
        with patch("UpdateCDFEntitiesAPI.check_unique_agency") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("agency_event.json")
            event["body"] = json.dumps(event["body"])
            message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_agy successfully updated",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_agency_uniqueness_failed():
    with patch("UpdateCDFEntitiesAPI.update_agency") as mock_ui:
        with patch("UpdateCDFEntitiesAPI.check_unique_agency") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (False, "Error: name already exists in agency")
            event = open_json_file("agency_event.json")
            event["body"] = json.dumps(event["body"])
            message = UpdateCDFEntitiesAPI.lambda_handler(event, None)
    assert message == {
        "statusCode": 400,
        "body": "Error: name already exists in agency",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_vehicle():
    with patch("UpdateCDFEntitiesAPI.update_vehicle") as mock_ui:
        mock_ui.return_value = (True, ok)
        event = open_json_file("vehicle_event.json")
        event["body"] = json.dumps(event["body"])
        message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_veh successfully updated",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_vehicle_failed():
    with patch("UpdateCDFEntitiesAPI.update_vehicle") as mock_ui:
        mock_ui.return_value = (False, "Failed update vehicle")
        event = open_json_file("vehicle_event.json")
        event["body"] = json.dumps(event["body"])
        message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed update vehicle",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_communicator():
    with patch("UpdateCDFEntitiesAPI.update_communicator") as mock_ui:
        with patch("UpdateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("commu_event.json")
            event["body"] = json.dumps(event["body"])
            message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_2100 successfully updated",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_communicator_failed():
    with patch("UpdateCDFEntitiesAPI.update_communicator") as mock_ui:
        with patch("UpdateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (False, "Failed update device")
            mock_check.return_value = (True, ok)
            event = open_json_file("commu_event.json")
            event["body"] = json.dumps(event["body"])
            message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed update device",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_ps():
    with patch("UpdateCDFEntitiesAPI.update_phaseselector") as mock_ui:
        with patch("UpdateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("ps_event.json")
            event["body"] = json.dumps(event["body"])
            message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_ps successfully updated",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_update_ps_failed():
    with patch("UpdateCDFEntitiesAPI.update_phaseselector") as mock_ui:
        with patch("UpdateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (False, "Failed update phaseselector")
            mock_check.return_value = (True, ok)
            event = open_json_file("ps_event.json")
            event["body"] = json.dumps(event["body"])
            message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed update phaseselector",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def mocked_requests_put(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse(None, 200)


def test_associate_vehicle_communicator():
    with patch("requests.put", side_effect=mocked_requests_put):
        event = open_json_file("associate_event.json")
        event["body"] = json.dumps(event["body"])
        message = UpdateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "Successfully associate zoeCommu with zoeVeh",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
