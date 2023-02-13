import pytest
import json
import os
import sys
import time
import boto3

from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth

from unittest.mock import patch

# allow tests to find all the code they needs to run
sys.path.append("../LambdaCode")
sys.path.append("../")
from CEI_RTRadio_Processing import lambda_handler


CDF_URL = os.environ["CDF_URL"]
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

# setup
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


def CDF_setup(data):
    """sets up the test entities within the CDF.
    [com_data, veh_data, agy_data, CEIagy_data, reg_data]
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
    region_call = json.dumps(data[4]).replace("'", '"').replace("|||", "'")
    CEIagency_call = json.dumps(data[3]).replace("'", '"').replace("|||", "'")
    agency_call = json.dumps(data[2]).replace("'", '"').replace("|||", "'")
    vehicle_call = json.dumps(data[1]).replace("'", '"').replace("|||", "'")
    com_call = json.dumps(data[0]).replace("'", '"').replace("|||", "'")

    # Get ID values

    vehicleName = data[1]["deviceId"]
    comID = data[0]["deviceId"]

    # Create Region
    # regionResults = requests.post(groupUrl, data=regionCall, headers=headers)
    region_results = send_request(
        groupUrl, "POST", os.environ["AWS_REGION"], params=region_call, headers=headers
    )
    time.sleep(2)
    # Create CEIAgency
    # agencyResults = requests.post(groupUrl, data=agencyCall, headers=headers)
    CEIagency_results = send_request(
        groupUrl,
        "POST",
        os.environ["AWS_REGION"],
        params=CEIagency_call,
        headers=headers,
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
    time.sleep(2)
    com_results = send_request(
        devicesUrl,
        "POST",
        os.environ["AWS_REGION"],
        params=com_call,
        headers=headers,
    )

    if not "204" in str(region_results.status_code):
        pytest.fail(
            f"Failed to set up Region - Response Code - { str(region_results)} Call - {region_call}"
        )
    if not "204" in str(CEIagency_results.status_code):
        pytest.fail(
            f"Failed to set up CEIagency_results - Response Code - { CEIagency_results.status_code } Call - {CEIagency_call}"
        )
    if not "204" in str(agency_results.status_code):
        pytest.fail(
            f"Failed to set up Agency - Response Code - { str(agency_results.status_code)} Call - {agency_call}"
        )
    if not "204" in str(vehicle_results.status_code):
        pytest.fail(
            f"Failed to set up Vehicle - Response Code - { str(vehicle_results.status_code)} Call - {vehicle_call}"
        )
    if not "204" in str(com_results.status_code):
        pytest.fail(
            f"Failed to set up Com - Response Code - { str(com_results.status_code)} Call - {com_call}"
        )

    create_association(vehicleName, comID)


def CDF_cleanup(data, closing=False):
    """cleans up the test entities within the CDF.
    [com_data, veh_data, agy_data, CEIagy_data, reg_data]
    Args:
        data (array[string]): Data to be removed from the CDF
            [0]: Vehicle Data
            [1]: Agency Data
            [2]: Region Data
        closing (boolean): Controls whether or not to fail the test


    """

    # Get ID values
    siteId = data[4]["name"]
    CEIagencyID = data[3]["name"]
    agencyID = data[2]["name"]
    vehicleName = data[1]["deviceId"]
    comID = data[0]["deviceId"]

    # Set up CDF URLs
    region_url = f"{CDF_URL}/groups/%2F{siteId}"
    ceiagency_url = f"{CDF_URL}/groups/%2F{siteId}%2F{CEIagencyID}"
    agency_url = f"{CDF_URL}/groups/%2F{siteId}%2F{agencyID}"
    vehicle_url = f"{CDF_URL}/devices/{vehicleName}"
    com_url = f"{CDF_URL}/devices/{comID}"
    # Remove test data

    com_results = send_request(
        com_url, "DELETE", os.environ["AWS_REGION"], headers=headers
    )

    vehicle_results = send_request(
        vehicle_url, "DELETE", os.environ["AWS_REGION"], headers=headers
    )

    agency_results = send_request(
        agency_url, "DELETE", os.environ["AWS_REGION"], headers=headers
    )

    CEIagency_results = send_request(
        ceiagency_url, "DELETE", os.environ["AWS_REGION"], headers=headers
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
        if not "204" in str(CEIagency_results.status_code):
            pytest.fail(
                f"Failed to clean up Vehicle - Response Code { str(vehicle_results)}"
            )
        if not "204" in str(vehicle_results.status_code):
            pytest.fail(
                f"Failed to clean up Vehicle - Response Code { str(vehicle_results)}"
            )
        if not "204" in str(com_results.status_code):
            pytest.fail(
                f"Failed to clean up Vehicle - Response Code { str(vehicle_results)}"
            )


def CDF_mock_data():
    """mocks up the data for the test via the names .json file.

    Returns:
        array[string]: results of operation
    """
    com_data = open_json_file("StandardCom.json", True)
    veh_data = open_json_file("CEIVehicle.json", True)
    agy_data = open_json_file("StandardAgency.json", True)
    CEIagy_data = open_json_file("CEIAgency.json", True)
    reg_data = open_json_file("CEIRegion.json", True)

    data = [com_data, veh_data, agy_data, CEIagy_data, reg_data]
    return data


def create_association(vehicle_device_id, com_device_id):
    association_url = (
        f"{CDF_URL}/devices/{vehicle_device_id}/installedat/out/devices/{com_device_id}"
    )

    association_result = send_request(
        association_url, "PUT", os.environ["AWS_REGION"], params=None, headers=headers
    )

    if association_result.status_code != 204:
        pytest.fail(
            f"Fail: Com/V2 Association - Response Code -{association_result.status_code}\n"
            f" {association_result.content.decode('utf-8')} \nURL - {association_url}"
        )


def test_setup():
    """Sets up the test entities within the CDF."""
    data = CDF_mock_data()
    CDF_cleanup(data, False)
    CDF_setup(data)


class fakeIoTPubSuccessResponse(object):
    """Placeholder for IoT Response

    Args:
        object ([type]): structural
    """

    def __init__(self):
        None


def test_activate():
    """Full process test of RTRadioMsg with active vehicle"""
    event = {
        "1617891005": {
            "atp.glat": 44.9512963,
            "atp.ghed": 19,
            "atp.glon": -92.9453703,
            "atp.gspd": 5,
            "atp.gpi": 4,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    mock_MQTTPostAndCache(event)


def test_no_activation():
    """Partial process test of RTRadioMsg with inactive vehicle"""
    event = {
        "1617891005": {
            "atp.glat": 44.9512963,
            "atp.ghed": 19,
            "atp.glon": -92.9453703,
            "atp.gspd": 5,
            "atp.gpi": 4,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    mock_MQTTPostAndCache(event, False)


def test_badTopic():
    """Error Catching Test - ensure bad topic results in desired error"""
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
        "topic": "derpitydoo",
    }
    with pytest.raises(Exception, match=r"Error - Malformed Topic"):
        mock_MQTTPostAndCache(event)

    return


def test_noLat():
    """Error Catching Test - ensure bad gps data without latitude results in desired error"""
    event = {
        "1617891005": {
            "atp.ghed": 19,
            "atp.glon": -92.9453703,
            "atp.gspd": 5,
            "atp.gpi": 4,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    with pytest.raises(Exception, match=r"Error - Malformed GPS Message"):
        mock_MQTTPostAndCache(event)


def test_noHeading():
    """Error Catching Test - ensure bad gps data without heading results in desired error"""
    event = {
        "1617891005": {
            "atp.glat": 44.9512963,
            "atp.ghed": 19,
            "atp.gspd": 5,
            "atp.gpi": 4,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    with pytest.raises(Exception, match=r"Error - Malformed GPS Message"):
        mock_MQTTPostAndCache(event)


def test_noSpeed():
    """Error Catching Test - ensure bad gps data without speed results in desired error"""
    event = {
        "1617891005": {
            "atp.glat": 44.9512963,
            "atp.ghed": 19,
            "atp.glon": -92.9453703,
            "atp.gpi": 4,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    with pytest.raises(Exception, match=r"Error - Malformed GPS Message"):
        mock_MQTTPostAndCache(event)


def test_noGPI():
    """Error Catching Test - ensure bad gps data without GPI results in desired error"""
    event = {
        "1617891005": {
            "atp.glat": 44.9512963,
            "atp.ghed": 19,
            "atp.glon": -92.9453703,
            "atp.gspd": 5,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    with pytest.raises(Exception, match=r"Error - Malformed GPS Message"):
        mock_MQTTPostAndCache(event)


def test_noLong():
    """Error Catching Test - ensure bad gps data without longitude results in desired error"""
    event = {
        "1617891005": {
            "atp.glat": 44.9512963,
            "atp.ghed": 19,
            "atp.gspd": 5,
            "atp.gpi": 4,
            "atp.gstt": 1,
            "atp.gsat": 3,
            "atp.gqal": 1,
        },
        "topic": "SW/CEI_RTR_Com/GTT/CEI/RTVEHDATA",
    }
    with pytest.raises(Exception, match=r"Error - Malformed GPS Message"):
        mock_MQTTPostAndCache(event)


def test_cleanup():
    """Remove the Test Objects from the CDF at the end of the sequence"""
    data = CDF_mock_data()
    CDF_cleanup(data, True)
    assert "Cleanup Successful"


def mock_MQTTPostAndCache(event, active=True):
    """Mock out IoT and Cache mechanisms
    Args:
        event (dictionary): Simulated message to be processed
        active (bool, optional): Weather or not the vehicle will be active. Defaults to True.

    """
    with patch("CEI_RTRadio_Processing.client.publish") as mock_mqtt_publish:
        with patch("CEI_RTRadio_Processing.get_vehicle_by_SN") as mock_cache:
            mock_mqtt_publish.return_value = fakeIoTPubSuccessResponse()
            vehicleResults = open_json_file("CacheRes.json", True)
            if active:
                vehicleResults["CEIVehicleActive"] = True
            else:
                vehicleResults["CEIVehicleActive"] = False
            mock_cache.return_value = vehicleResults
            lambda_handler(event, None)
