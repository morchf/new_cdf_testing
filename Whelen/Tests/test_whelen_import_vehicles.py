import json
import os
import time
import sys
import boto3
import pytest


from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session

# defaults -
CDF_URL = "https://oo9fn5p38b.execute-api.us-east-1.amazonaws.com"
AWS_REGION = "us-east-1"
FEATURE_PERSISTENCE_URL = (
    "https://k02hcsidw5.execute-api.us-east-1.amazonaws.com/develop"
)
WHELEN_SERVERLESS_API_URL = (
    "https://ott85lv4g9.execute-api.us-east-1.amazonaws.com/develop"
)

expectedComIds = [
    "231409a0-b5d5-11ec-af2c-e70c2d4a6e57",
    "33a7c120-b5db-11ec-ba17-93ba7eb542e8",
    "3496db60-afa1-11ec-bf62-3bdab4e03f04",
    "34e84140-b437-11ec-aa85-05649929c363",
    "381dc660-b67f-11ec-9dc2-177f0b9a7163",
    "3d336770-b438-11ec-b0e5-4fa264f7c54f",
    "4dc64460-b5da-11ec-ba17-93ba7eb542e8",
    "6f643980-b452-11ec-90c4-274c874ca95b",
    "7dc8c2a0-b521-11ec-9e8e-fdef76c74cfe",
    "953a1750-b50c-11ec-bc65-8bcd27b789b3",
    "9bf023d0-b437-11ec-b0e5-4fa264f7c54f",
    "a06c41b0-b5da-11ec-ba17-93ba7eb542e8",
    "bf2f10b0-b67e-11ec-8881-8b345c80834f",
    "c94a91d0-b455-11ec-af22-57cf2a8bc27b",
    "d9ffd5a0-b50c-11ec-bc65-8bcd27b789b3",
    "f92427e0-b437-11ec-b0e5-4fa264f7c54f",
    "fcb13850-b67e-11ec-9dc2-177f0b9a7163",
]

if os.environ.get("CDF_URL", None) is not None:
    CDF_URL = os.environ["CDF_URL"]
    print(f"CDF_URL found, set to {CDF_URL}")

if os.environ.get("AWS_REGION", None) is not None:
    AWS_REGION = os.environ["AWS_REGION"]
    print(f"AWS_REGION found, set to {AWS_REGION}")

if os.environ.get("feature_persistence_url", None) is not None:
    FEATURE_PERSISTENCE_URL = os.environ["feature_persistence_url"]
    print(f"feature_persistence_url found, set to {FEATURE_PERSISTENCE_URL}")

if os.environ.get("WHELEN_SERVERLESS_API_URL", None) is not None:
    WHELEN_SERVERLESS_API_URL = os.environ["WHELEN_SERVERLESS_API_URL"]
    print(f"WHELEN_SERVERLESS_API_URL found, set to {WHELEN_SERVERLESS_API_URL}")


TEST_IMPORT_GUID = "6dee280a-09ce-11ed-87aa-42e419a585ab"

group_url = f"{CDF_URL}/groups/"
devices_url = f"{CDF_URL}/devices/"
import_url = f"{WHELEN_SERVERLESS_API_URL}/importvehicles"
activate_url = f"{WHELEN_SERVERLESS_API_URL}/changepreemption"


client = boto3.client("dynamodb")
dynamodb = boto3.resource("dynamodb")

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}


def send_request(url, method, region_name, params=None, headers=None):
    """Send an http request to AWS with all applicable fields

    Args:
        url (string): target url for call - API Endpoint
        method (string): "DELETE," "GET," or "POST"
        region_name (string): Target AWS Region
        params (string, optional): call body - may be blank for GET and DELETE calls. Defaults to None.
        headers (string, optional): http headers. Defaults to None.

    Returns:
        _type_: call result
    """
    print(f"AWS_REGION = {AWS_REGION}")
    session = boto3.session.Session(region_name=AWS_REGION)
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(session.get_credentials(), "execute-api", region_name).add_auth(
        request
    )  # noqa: E501
    return URLLib3Session().send(request.prepare())


def open_json_file(file_name, subQuotes=False):
    """opens and reads in the necessary json files for setup.

    Args:
        filename (dictionary): name of json file to be processed

    Returns:
        string: results of operation
    """
    json_str = None

    if os.path.exists(os.path.join(sys.path[0], file_name)):
        with open(os.path.join(sys.path[0], file_name), "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "")
        if subQuotes:
            json_str = json_str.replace("'", "|||")
    else:
        print(f"{file_name} not found.")
    json_obj = json.loads(json_str)
    return json_obj


def create_region(file_name):
    """Create the test agency in the CDF for

    Args:
        file_name (string): name of source file for agency

    Returns:
        agency_data: attribute data of agency created
    """
    region_data = open_json_file(file_name, True)
    region_call = json.dumps(region_data).replace("'", '"')

    # creating region
    region_result = send_request(
        group_url, "POST", AWS_REGION, params=region_call, headers=headers
    )

    if region_result.status_code != 204:
        pytest.fail(
            f"Failed to set up Region - Response Code -{region_result.status_code}\n"
            f"{region_result.content.decode('utf-8')} \nCall - {region_call}"
        )
    return region_data


def create_agency(file_name):
    """Create the test agency in the CDF for

    Args:
        file_name (string): name of source file for agency

    Returns:
        agency_data: attribute data of agency created
    """
    agency_data = open_json_file(file_name, True)
    agency_call = json.dumps(agency_data).replace("'", '"')

    # Creating agency
    agency_result = send_request(
        group_url, "POST", AWS_REGION, params=agency_call, headers=headers
    )

    if agency_result.status_code != 204:
        pytest.fail(
            f"Failed to set up Agency - Response Code -{agency_result.status_code}\n"
            f"{agency_result.content.decode('utf-8')} \nCall - {agency_call}"
        )
    return agency_data


def confirm_com(com_name, confirmState=False, state=""):
    """Confirm that a given com is in the CDF, if desired, confirm that the preemptionLicense
    is of a designated state -"pending", "inactive", "active", "decommissioned",  or "transferred"

    Args:
        com_name (guid): comID of desired vehicle
        confirmState (bool, optional): If True, Check Preemption License Defaults to False.
        state (str, optional): intended preemptionLicense value to check for. Defaults to "".
    """
    get_com_call = f"{devices_url}{com_name}"
    get_com_result = send_request(
        get_com_call, "GET", AWS_REGION, None, headers=headers
    )
    data = get_com_result.content.decode("utf-8")
    # print(f"Result = {get_com_result.content.decode('utf-8')}")
    if get_com_result.status_code != 200:
        pytest.fail(
            f"Confirmation Failed {com_name} - Response Code -{get_com_result.status_code}\n"
            f"{get_com_result.content.decode('utf-8')} \nCall - {get_com_call}"
        )
    if confirmState:
        preemptionState = json.loads(data).get("attributes").get("preemptionLicense")
        if preemptionState:
            if preemptionState != state:
                pytest.fail(
                    f"Confirmation Failed {com_name} - Seeking preemptionLicense {state}, returned {preemptionState}\n"
                    f"{get_com_result.content.decode('utf-8')} \nCall - {get_com_call}"
                )
        else:
            pytest.fail(
                f"Confirmation Failed {com_name} - Unable to retrieve preemptionLicense\n"
                f"{get_com_result.content.decode('utf-8')} \nCall - {get_com_call}"
            )


def get_featurePersistence_existence(agency_guid):
    """confirm the existence of the underlying import agency in the feature persistence DB
    if present, great. If not, put it there.

    Args:
        agency_guid (guid): guid of import target agency
    """
    if is_valid_guid(agency_guid):
        return
    else:
        insert_feature_persistence_entry(agency_guid)
        if not is_valid_guid(agency_guid):
            pytest.fail(
                f"Failed establishment of FeaturePersistence entry - agency_guid {agency_guid}"
            )


def is_valid_guid(agency_guid) -> bool:
    """Given an agency guid, check if its present in feature persistence. Then allow the script to proceed if it is..

    Args:
        agency_guid (String): GUID of the agency

    Returns:
        bool: true if guid in feature persistence
    """
    present = False
    try:
        url = (
            FEATURE_PERSISTENCE_URL
            + "?AgencyGUID="
            + agency_guid.upper()
            + "&FeatureName=whelen"
        )
        response = send_request(
            url, method="GET", region_name=os.environ["AWS_REGION"], headers=headers
        )
        status_code = response.status_code
        if status_code == 200:
            present = True

    except Exception as e:
        print(f"Error: in fetching information from Feature Persistence: {e}")
    return present


def insert_feature_persistence_entry(agency_guid):
    """insert the necessary entry into the feature persistence table to accomidate the whelen testing

    Args:
        agency_guid (GUID): guid ID of the agency in question.

    Raises:
        e: if the insert fails, describe and report
    """
    table = dynamodb.Table("FeaturePersistence")
    try:
        entry = {
            "AgencyGUId": agency_guid,
            "FeatureName": "whelen",
            "Feature": {
                "vehicle_positions_url": {"S": "Whelen's vehicle_positions_url"},
                "api_endpoint": {
                    "S": "https://laxksv26yj.execute-api.us-west-2.amazonaws.com/prod/gtt/vehicles"
                },
                "X-Api-Key": {"S": "WqmNKxBuaB7qPGpSCMUcv6hHaekNAKocaGGEtt8n"},
                "accessKey": {"S": "eddcbc44-1a34-4917-b4c4-c67fdce289ff"},
                "trip_updates_url": {"S": "Whelen's trip_updates_url"},
            },
        }
        table.put_item(Item=entry)

    except Exception as e:
        print(f"Error: failed to create feature persistence entry: {e}")
        raise e


def delete_region(region_name):
    region_url = f"{CDF_URL}/groups/%2F{region_name}"

    region_result = send_request(region_url, "DELETE", AWS_REGION, headers=headers)

    if region_result.status_code != 204:
        if region_result.status_code != 404:
            pytest.fail(
                f"Failed to clean up Region - Response Code -{region_result.status_code}\n"
                f"{region_result.content.decode('utf-8')}"
            )


def delete_agency(region_name, agency_name):
    agency_url = f"{CDF_URL}/groups/%2F{region_name}%2F{agency_name}"

    agency_result = send_request(agency_url, "DELETE", AWS_REGION, headers=headers)

    if agency_result.status_code != 204:
        if agency_result.status_code != 404:
            pytest.fail(
                f"Failed to clean up Agency - Response Code -{agency_result.status_code}\n"
                f"{agency_result.content.decode('utf-8')}"
            )


def delete_com(com_device_id, test=False):
    com_url = f"{CDF_URL}/devices/{com_device_id}"

    com_result = send_request(com_url, "DELETE", AWS_REGION, headers=headers)

    if test:
        if com_result.status_code != 204:
            pytest.fail(
                f"Failed to clean up Com - Response Code -{com_result.status_code}\n"
                f"{com_result.content.decode('utf-8')}"
            )


def test_setup():
    test_cleanup()
    create_region("WhelenTestImportRegion.json")
    create_agency("WhelenTestImportAgency.json")
    get_featurePersistence_existence(TEST_IMPORT_GUID)


def test_import():
    import_call = f"{import_url}?agency_guid={TEST_IMPORT_GUID}"
    print(f"import_call = {import_call}")
    com_result = send_request(
        import_call, "POST", AWS_REGION, params=None, headers=headers
    )
    print(f"import_call com_result = {com_result.status_code}")
    if com_result.status_code != 202:
        pytest.fail(
            f"Import Call failed - Response Code -{com_result.status_code}\n"
            f"{com_result.content.decode('utf-8')}"
        )
    time.sleep(20)
    for id in expectedComIds:
        confirm_com(id)


def test_activate_vehicle():
    print(f"activate_url = {activate_url}")
    data = json.dumps(open_json_file("ActivationCall.json"))
    com_result = send_request(
        activate_url,
        "POST",
        AWS_REGION,
        params=data,
        headers=headers,
    )
    print(
        f"activate_call com_result = {com_result.status_code}, {com_result.content.decode('utf-8')}"
    )
    if com_result.status_code != 202:
        pytest.fail(
            f"Import Call failed - Response Code -{com_result.status_code}\n"
            f"{com_result.content.decode('utf-8')}"
        )
    time.sleep(20)
    confirm_com("231409a0-b5d5-11ec-af2c-e70c2d4a6e57", True, "active")


def test_deactivate_vehicle():
    print(f"activate_url = {activate_url}")
    data = json.dumps(open_json_file("DeactivationCall.json"))
    com_result = send_request(
        activate_url,
        "POST",
        AWS_REGION,
        params=data,
        headers=headers,
    )
    print(
        f"activate_call com_result = {com_result.status_code}, {com_result.content.decode('utf-8')}"
    )
    if com_result.status_code != 202:
        pytest.fail(
            f"Import Call failed - Response Code -{com_result.status_code}\n"
            f"{com_result.content.decode('utf-8')}"
        )
    time.sleep(20)
    confirm_com("231409a0-b5d5-11ec-af2c-e70c2d4a6e57", True, "inactive")


def test_cleanup():
    for id in expectedComIds:
        delete_com(id, True)
    delete_agency("WhelenTestImportRegion", "WhelenTestImportAgency")
    delete_region("WhelenTestImportRegion")
