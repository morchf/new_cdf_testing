# flake8: noqa
# fmt: off
import pytest
import json
import os
import time
from importlib import reload
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
import boto3
from unittest.mock import patch
from CEI_Logging import post_log

CDF_URL = os.environ["CDF_URL"]
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}


class fakeSuccessResponse(object):
    def __init__(self):
        self.FailedPutCount = 204
        self.Encrypted = True
        self.RequestResponses = [
            {"RecordId": "string", "ErrorCode": "string", "ErrorMessage": "string"}
        ]


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    return URLLib3Session().send(request.prepare())


def open_json_file(file_name, subQuotes):
    """opens and reads in the necessary json files for setup.

    Args:
        filename (dictionary): name of json file to be processed

    Returns:
        string: results of operation
    """
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "")
        if subQuotes:
            json_str = json_str.replace("'", "|||")
    else:
        print(f"{file_name} not found.")
    json_obj = json.loads(json_str)
    return json_obj


def CDF_mock_data():
    """mocks up the data for the test via the names .json file.

    Returns:
        array[string]: results of operation
    """
    device_data = open_json_file("CEIVehicle.json", True)
    agy_data = open_json_file("CEIAgency.json", True)
    reg_data = open_json_file("CEIRegion.json", True)

    data = [device_data, agy_data, reg_data]
    return data


def CDF_setup(data):
    """sets up the test entities within the CDF.

    Args:
        data (array[string]): Data tp be added to the CDF
            [0]: Vehicle Data
            [1]: Agency Data
            [2]: Region Data
    Returns:
        array[string]: results of operation
            [0]: Vehicle Data
            [1]: Agency Data
            [2]: Region Data
    """

    # set up URLs
    groupUrl = f"{CDF_URL}/groups/"
    devicesUrl = f"{CDF_URL}/devices/"

    # Clean up json for ' vs. " conflicts
    region_call = json.dumps(data[2]).replace("'", '"').replace("|||", "'")
    agency_call = json.dumps(data[1]).replace("'", '"').replace("|||", "'")
    vehicle_call = json.dumps(data[0]).replace("'", '"').replace("|||", "'")

    # Create Region
    # regionResults = requests.post(groupUrl, data=regionCall, headers=headers)
    region_results = send_request(
        groupUrl, "POST", os.environ["AWS_REGION"], params=region_call, headers=headers
    )
    time.sleep(2)
    # Create Agency
    # agencyResults = requests.post(groupUrl, data=agencyCall, headers=headers)
    agency_results = send_request(
        groupUrl, "POST", os.environ["AWS_REGION"], params=agency_call, headers=headers
    )
    time.sleep(2)
    # Create Vehicle
    # vehicleResults = requests.post(devicesUrl, data=vehicleCall, headers=headers)
    vehicle_results = send_request(
        devicesUrl,
        "POST",
        os.environ["AWS_REGION"],
        params=vehicle_call,
        headers=headers,
    )

    if not "204" in str(region_results.status_code):
        pytest.fail(
            f"Failed to set up Region - Response Code - { str(region_results)} Call - {region_call}"
        )
    if not "204" in str(agency_results.status_code):
        pytest.fail(
            f"Failed to set up Agency - Response Code - { str(agency_results)} Call - {agency_call}"
        )
    if not "204" in str(vehicle_results.status_code):
        pytest.fail(
            f"Failed to set up Vehicle - Response Code - { str(vehicle_results)} Call - {vehicle_call}"
        )
    creationResults = [region_results, agency_results, vehicle_results]
    return creationResults


def CDF_cleanup(data, closing):
    """cleans up the test entities within the CDF.

    Args:
        data (array[string]): Data to be removed from the CDF
            [0]: Vehicle Data
            [1]: Agency Data
            [2]: Region Data
        closing (boolean): Controls whether or not to fail the test

    Returns:
        array[string]: results of operation
            [0]: Vehicle Data
            [1]: Agency Data
            [2]: Region Data
    """

    # Get ID values
    siteId = data[2]["name"]
    agencyID = data[1]["name"]
    vehicleName = data[0]["deviceId"]

    # Set up CDF URLs
    region_url = f"{CDF_URL}/groups/%2F{siteId}"
    agency_url = f"{CDF_URL}/groups/%2F{siteId}%2F{agencyID}"
    vehicle_url = f"{CDF_URL}/devices/{vehicleName}"

    # Remove test data

    vehicle_results = send_request(
        vehicle_url, "DELETE", os.environ["AWS_REGION"], headers=headers
    )

    agency_results = send_request(
        agency_url, "DELETE", os.environ["AWS_REGION"], headers=headers
    )

    region_results = send_request(
        region_url, "DELETE", os.environ["AWS_REGION"], headers=headers
    )

    if closing:
        if not "204" in str(region_results.status_code):
            pytest.fail(
                f"Failed to clean up Region - Response Code { str(region_results)}"
            )
        if not "204" in str(agency_results.status_code):
            pytest.fail(
                f"Failed to clean up Agency - Response Code { str(agency_results)}"
            )
        if not "204" in str(vehicle_results.status_code):
            pytest.fail(
                f"Failed to clean up Vehicle - Response Code { str(vehicle_results)}"
            )
    cleanup = [region_results, agency_results, vehicle_results]
    return cleanup


def test_setup():
    """Sets up the test entities within the CDF."""
    data = CDF_mock_data()
    CDF_cleanup(data, False)
    CDF_setup(data)


def test_post_no_agency():
    """Test Post Log Call with no associated agency value"""
    result = mockedLog(
        "CEI_EtE_TestRegion",
        None,
        "CEI_EtE_TestVehicle_Id"
    )
    assert "Error" not in result


def test_post_agency():
    """Test Post Log Call with all associated values"""
    result = mockedLog(
        "CEI_EtE_TestRegion",
        "CEI_EtE_TestAgency",
        "CEI_EtE_TestVehicle_Id"
    )
    assert "Error" not in result


def test_post_no_devId():
    """Test Post Log Call with no associated device id value"""
    result = mockedLog(
        "CEI_EtE_TestRegion",
        "CEI_EtE_TestAgency",
        None
    )
    assert "Error" not in result


def test_CDF_Failure(monkeypatch):
    """Test Post Log call with broken CDF

    Args:
        monkeypatch (monkeypatch referece): monkeypatch used to alter the CDF_URL value
    """
    monkeypatch.setenv("CDF_URL", "NullCDFUrl")

    # reload the configuration processing lambda so it uses the new CDF_URL
    from CEI_Logging import post_log

    result = mockedLog(
        "CEI_EtE_TestRegion",
        "CEI_EtE_TestAgency",
        "CEI_EtE_TestVehicle_Id"
    )
    assert "Error" not in result


def mockedLog(
    site_id,
    agency_id,
    device_CEI_id
):
    """Fire a mocked version of the post-log command, subbing out the actual boto3 firehose piece

    Args:
        site_id (string): region identifdier
        agency_id (string): agency identifier
        device_CEI_id (string): device identifier

    Returns:
        string: result of mock test
    """
    with patch("CEI_Logging.client.put_record_batch") as mock_postLog_post:
        mock_postLog_post.return_value = fakeSuccessResponse()
        result = post_log(
            site_id,
            agency_id,
            device_CEI_id,
            "Test",
            "Test",
            "Test",
            "Test",
            "Test",
        )
    return result


def test_cleanup():
    """Remove the Test Objects from the CDF at the end of the sequence"""
    data = CDF_mock_data()
    CDF_cleanup(data, True)
    assert "Cleanup Successful"
