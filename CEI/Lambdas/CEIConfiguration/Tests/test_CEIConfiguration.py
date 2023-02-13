import pytest
import json
import os
import sys
import time
from importlib import reload
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
import boto3

# allow tests to find all the code they need to run
sys.path.append("../LambdaCode")
sys.path.append("../")
from CEI_Configuration import configurationHandler

CDF_URL = os.environ["CDF_URL"]
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}


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


def open_json_file(file_name, subQuotes=False):
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


def test_configurationAssignmentTest():
    """Basic configuration assignment test -
    fails if the CDF cannot be reached/does not respond with 200
    fails if any of the fields within configuration_success_call.json do NOT successfully get assigned in the CDF

    """

    data = open_json_file("ConfigurationSuccessCall.json", False)
    site_id = data["siteId"]
    agency_id = data["agencyId"]
    data_call = json.dumps(data).replace("'", '"').replace("|||", "'").replace("|", "")

    url_action = f"/groups/%2F{site_id}%2F{agency_id}"
    url_complete = f"{CDF_URL}/{url_action}"

    response = configurationHandler(json.loads(data_call), None)

    # fail if the lambda call was unsuccessful
    if "200" not in str(response):
        print(str(response))
        pytest.fail(
            f"Unable to test configuration call. Response: {str(response)} \r\n\r\n Call: {data_call}"
        )

    agency = send_request(
        url_complete, "GET", os.environ["AWS_REGION"], headers=headers
    ).content
    agency = json.loads(agency)["attributes"]
    failures = []
    # check each field value against the CDF
    if str(agency["CEIUnitIDConfig"]) != str(data["unitIDConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIUnitIDConfig- {agency['CEIUnitIDConfig']} \r\n File Value - {data['unitIDConfig']}"
        )

    if str(agency["CEIUnitTypeConfig"]) != str(data["unitTypeConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIUnitTypeConfig - {agency['CEIUnitTypeConfig']} \r\n File Value - {data['unitTypeConfig']}"
        )

    if str(agency["CEIIncidentTypeConfig"]) != str(data["incidentTypeConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentTypeConfig - {agency['CEIIncidentTypeConfig']} \r\n File Value - {data['incidentTypeConfig']}"
        )

    if str(agency["CEIIncidentTypeConfig"]) != str(data["incidentTypeConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentTypeConfig - {agency['CEIIncidentTypeConfig']} \r\n File Value - {data['incidentTypeConfig']}"
        )

    if str(agency["CEIIncidentStatusConfig"]) != str(data["incidentStatusConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentStatusConfig - {agency['CEIIncidentStatusConfig']} \r\n File Value - {data['incidentStatusConfig']}"
        )

    if str(agency["CEIIncidentPriorityConfig"]) != str(data["incidentPriorityConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentPriorityConfig - {agency['CEIIncidentPriorityConfig']} \r\n File Value - {data['incidentPriorityConfig']}"
        )

    if str(agency["CEIUnitStatusConfig"]) != str(data["unitStatusConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIUnitStatusConfig - {agency['CEIUnitStatusConfig']} \r\n File Value - {data['unitStatusConfig']}"
        )

    if len(failures) > 0:
        print(*failures, sep="\n")
        pytest.fail(str(failures), True)


def test_msgFormatFailureTest():
    """Test that the configuration call handles msg format failures gracefully
    Fails if the resulting response is anything other than 400.
    """
    from CEI_Configuration import configurationHandler

    data = open_json_file("ConfigurationFailureCall.json", False)
    dataCall = json.dumps(data).replace("'", '"').replace("|||", "'").replace("|", "")

    response = configurationHandler(json.loads(dataCall), None)

    # fail if the lambda doesn't return the desired 400 error
    if "400" not in str(response):
        failureMsg = f"Failed to properly catch the message key Response: {str(response)} \r\n\r\n Call: {dataCall}"
        print(failureMsg)
        pytest.fail(failureMsg)


def test_CDF_failure_test(monkeypatch):
    """Test that the configuration call handles msg format failures gracefully
    Fails if the resulting response is anything other than 400.

    Args:
    monkeypatch - patch to alter the CDF_URL to break the connection functionality
    """

    data = open_json_file("ConfigurationSuccessCall.json", False)
    data_call = json.dumps(data).replace("'", '"').replace("|||", "'").replace("|", "")
    print({os.environ["CDF_URL"]})

    monkeypatch.setenv("CDF_URL", "NullCDFUrl")

    # reload the configuration processing lambda so it uses the new CDF_URL
    from CEI_Configuration import configurationHandler

    reload(sys.modules["CEI_Configuration"])

    response = configurationHandler(json.loads(data_call), None)

    # fail if the lambda doesn't return the desired 500 error
    if "500" not in str(response):
        failureMsg = f"Failed to properly catch the broken connection response: {str(response)} \r\n\r\n Call: {data_call} \r\n\r\n {os.environ['CDF_URL']}"
        print(failureMsg)
        pytest.fail(failureMsg)


def test_cleanup():
    """Remove the Test Objects from the CDF at the end of the sequence"""
    data = CDF_mock_data()
    CDF_cleanup(data, True)
    assert "Cleanup Successful"
