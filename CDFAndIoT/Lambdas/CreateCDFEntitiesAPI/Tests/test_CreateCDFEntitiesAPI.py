import json
import os
import sys
from unittest.mock import patch, PropertyMock
import boto3
from moto import mock_ssm

sys.path.append("../LambdaCode")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"
os.environ["AWS_REGION"] = "us-east-1"

import CreateCDFEntitiesAPI  # noqa: E402

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


def test_get_modem_data():
    # Check for data retrieval with valid SN
    with patch("CreateCDFEntitiesAPI.urllib3.PoolManager.request") as mock_url:
        with mock_ssm():
            client = boto3.client("ssm", os.environ["AWS_REGION"])
            client.put_parameter(Name="SW-API-username", Value="name", Type="String")
            client.put_parameter(Name="SW-API-password", Value="psswrd", Type="String")
            client.put_parameter(Name="SW-API-client-ID", Value="13579", Type="String")
            client.put_parameter(
                Name="SW-API-client-secret", Value="scrt", Type="String"
            )
            client.put_parameter(
                Name="SW-API-GTT-Company-Number", Value="2222", Type="String"
            )

            type(mock_url.return_value).data = PropertyMock(
                side_effect=[
                    json.dumps({"access_token": "token"}),
                    json.dumps({"items": "things"}),
                ]
            )

            serialNumber = "N684570206021035"
            data = CreateCDFEntitiesAPI.get_modem_data(serialNumber)
    assert data == "things"


def test_get_modem_data_invalid_SN():
    # Check for no data retrieval with invalid SN
    with patch("CreateCDFEntitiesAPI.urllib3.PoolManager.request") as mock_url:
        with mock_ssm():
            client = boto3.client("ssm", os.environ["AWS_REGION"])
            client.put_parameter(Name="SW-API-username", Value="name", Type="String")
            client.put_parameter(Name="SW-API-password", Value="psswrd", Type="String")
            client.put_parameter(Name="SW-API-client-ID", Value="13579", Type="String")
            client.put_parameter(
                Name="SW-API-client-secret", Value="scrt", Type="String"
            )
            client.put_parameter(
                Name="SW-API-GTT-Company-Number", Value="2222", Type="String"
            )
            type(mock_url.return_value).data = PropertyMock(
                side_effect=[json.dumps({"access_token": "token"}), None]
            )
            serialNumber = "blah"
            data = CreateCDFEntitiesAPI.get_modem_data(serialNumber)
    assert not data


def test_create_region():
    with patch("CreateCDFEntitiesAPI.new_region") as mock_ui:
        mock_ui.return_value = (True, ok)
        event = open_json_file("region_event.json")
        event["body"] = json.dumps(event["body"])
        message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_reg successfully created!",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_region_failed():
    with patch("CreateCDFEntitiesAPI.new_region") as mock_ui:
        mock_ui.return_value = (False, "Failed create region")
        event = open_json_file("region_event.json")
        event["body"] = json.dumps(event["body"])
        message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed create region",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_agency():
    with patch("CreateCDFEntitiesAPI.new_agency") as mock_ui:
        with patch("CreateCDFEntitiesAPI.check_unique_agency") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("agency_event.json")
            event["body"] = json.dumps(event["body"])
            message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_agy successfully created!",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_agency_uniqueness_failed():
    with patch("CreateCDFEntitiesAPI.new_agency") as mock_ui:
        with patch(
            "CreateCDFEntitiesAPI.check_unique_agency",
            side_effect=Exception("Error: agencyCode already exists in agency"),
        ):
            mock_ui.return_value = (True, ok)
            event = open_json_file("agency_event.json")
            event["body"] = json.dumps(event["body"])
            message = CreateCDFEntitiesAPI.lambda_handler(event, None)
    assert message == {
        "statusCode": 400,
        "body": "Error: agencyCode already exists in agency",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_vehicle():
    with patch("CreateCDFEntitiesAPI.new_vehicle") as mock_ui:
        mock_ui.return_value = (True, ok)
        event = open_json_file("vehicle_event.json")
        event["body"] = json.dumps(event["body"])
        message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_veh successfully created!",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_vehicle_failed():
    with patch("CreateCDFEntitiesAPI.new_vehicle") as mock_ui:
        mock_ui.return_value = (False, "Failed create vehicle")
        event = open_json_file("vehicle_event.json")
        event["body"] = json.dumps(event["body"])
        message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed create vehicle",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_communicator():
    with patch("CreateCDFEntitiesAPI.new_communicator") as mock_ui:
        with patch("CreateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("commu_event.json")
            event["body"] = json.dumps(event["body"])
            message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_2100 successfully created!",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_communicator_failed():
    with patch("CreateCDFEntitiesAPI.new_communicator") as mock_ui:
        with patch("CreateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (False, "Failed create device")
            mock_check.return_value = (True, ok)
            event = open_json_file("commu_event.json")
            event["body"] = json.dumps(event["body"])
            message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed create device",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_ps():
    with patch("CreateCDFEntitiesAPI.new_phaseselector") as mock_ui:
        with patch("CreateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("ps_event.json")
            event["body"] = json.dumps(event["body"])
            message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "zoe_ps successfully created!",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_create_ps_failed():
    with patch("CreateCDFEntitiesAPI.new_phaseselector") as mock_ui:
        with patch("CreateCDFEntitiesAPI.check_unique_device") as mock_check:
            mock_ui.return_value = (False, "Failed create phaseselector")
            mock_check.return_value = (True, ok)
            event = open_json_file("ps_event.json")
            event["body"] = json.dumps(event["body"])
            message = CreateCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 400,
        "body": "Failed create phaseselector",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
