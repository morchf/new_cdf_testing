# flake8: noqa
# fmt: off
import sys
import pytest
import json
import os
import requests
import time
import boto3
import uuid
import requests.auth
from boto3.dynamodb.conditions import Key
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
sys.path.append("../../CEIBackend")
from CEI_Dynamo_Cache import get_vehicle_by_all_cei_vals

# client = boto3.client('dynamodb')

CDF_URL = os.environ["CDF_URL"]
AWS_REGION = os.environ["AWS_REGION"]

DYNAMODB = boto3.resource("dynamodb")
SQS = boto3.resource("sqs")

group_url = f"{CDF_URL}/groups/"
devices_url = f"{CDF_URL}/devices/"

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}


# Send request to AWS using aws signature 

def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(method=method.upper(), url=url, data=params, headers=headers)
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    return URLLib3Session().send(request.prepare())


def def_get_cognito_auth():
    """get the api cognito authentication from the secrets manager.
        CANCEL all subsequent testing and cleanup CDF in the event
         of a failure - all fields are necessary.
    Returns:
        [dictionary]: cognito app client id and secret
        (CEIDevAppClientID, CEIDevAppClientSecret, CEIAPIURL, CEIAuthURL)
    """
    secret_name = "CEIDevAppClientInfo"

    session = boto3.session.Session()
    region_name = session.region_name
    retrieval_success = True
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception:
        retrieval_success = False
    else:
        # Decrypts secret using the associated KMS CMK.
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
    if secret is None:
        retrieval_success = False

    results = json.loads(secret)
    if (
        results.get("CEIDevAppClientID", None) is None
        or results.get("CEIDevAppClientSecret", None) is None
        or results.get("CEIAPIURL", None) is None
        or results.get("CEIAuthURL", None) is None
    ):
        retrieval_success = False
    if not retrieval_success:
        # data = CDF_mock_data()
        # CDF_cleanup(data, True)
        pytest.exit(
            "Failed to retrieve Secrets -"
            + " ensure cognito authorization is properly stored"
            + "(name = CEIDevAppClientInfo, keys ="
            + " CEIDevAppClientId, CEIDevAppClientSecret, CEIAPIURL, CEIAuthURL)"
        )

    return json.loads(secret)


## reading test data json file

def open_json_file(file_name, subQuotes):
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
    region_data = open_json_file(file_name, True)
    region_call = json.dumps(region_data).replace("'", '"').replace("|||", "'")
    

    #creating region
    region_result = send_request(
        group_url, "POST", AWS_REGION, params = region_call, headers = headers
    )

    if region_result.status_code != 204:
        pytest.fail(
            f"Failed to set up Region - Response Code -{region_result.status_code}\n"
            f"{region_result.content.decode('utf-8')} \nCall - {region_call}"
        )
    return region_data

def create_agency(file_name):
    agency_data = open_json_file(file_name, True)
    agency_call = json.dumps(agency_data).replace("'", '"').replace("|||", "'")

    #Creating agency
    agency_result = send_request(
        group_url, "POST", AWS_REGION, params=agency_call, headers=headers
    )

    if agency_result.status_code !=204:
        pytest.fail(
            f"Failed to set up Agency - Response Code -{agency_result.status_code}\n"
            f"{agency_result.content.decode('utf-8')} \nCall - {agency_call}"
        )
    return agency_data

def create_vehicle(file_name):
    vehicle_data = open_json_file(file_name, True)
    vehicle_call = json.dumps(vehicle_data).replace("'", '"').replace("|||", "'")

    #Creating Vehicle

    vehicle_result = send_request(
        devices_url, "POST", AWS_REGION, params=vehicle_call, headers=headers
    )

    if vehicle_result.status_code !=204:
        pytest.fail(
            f"Failed to set up V2 Vehicle - Response Code -{vehicle_result.status_code}\n"
            f"{vehicle_result.content.decode('utf-8')} \nCall - {vehicle_call}"
        )
    return vehicle_data

def create_com(file_name):
    com_data = open_json_file(file_name, True)
    com_call = json.dumps(com_data).replace("'", '"').replace("|||", "'")

    #Creating com

    com_result = send_request(
        devices_url, "POST", AWS_REGION, params=com_call, headers=headers
    )

    if com_result.status_code != 204:
        pytest.fail(
            f"Failed to set up com - Response Code -{com_result.status_code}\n"
            f"{com_result.content.decode('utf-8')} \nCall - {com_call}"
        )
    return com_data

def create_association(vehicle_device_id, com_device_id):
    association_url = (
        f"{CDF_URL}/devices/{vehicle_device_id}/installedat/out/devices/{com_device_id}"
    )

    association_result = send_request(
        association_url, "PUT", AWS_REGION, params=None, headers=headers
    )

    if association_result.status_code !=204:
        pytest.fail(
            f"Fail: Com/V2 Association - Response Code -{association_result.status_code}\n"
            f" {association_result.content.decode('utf-8')} \nURL - {association_url}"
        )

def delete_region(region_name):
    region_url = f"{CDF_URL}/groups/%2F{region_name}"

    region_result = send_request(
        region_url, "DELETE", AWS_REGION, headers = headers
    )

    if region_result.status_code != 204:
        if region_result.status_code != 404:
            pytest.fail(
                    f"Failed to clean up Region - Response Code -{region_result.status_code}\n"
                    f"{region_result.content.decode('utf-8')}"
                )

def delete_agency(region_name, agency_name):
    agency_url = f"{CDF_URL}/groups/%2F{region_name}%2F{agency_name}"

    agency_result = send_request(
        agency_url, "DELETE", AWS_REGION, headers=headers
    )

    if agency_result.status_code != 204:
        if agency_result.status_code != 404:
            pytest.fail(
                    f"Failed to clean up Agency - Response Code -{agency_result.status_code}\n"
                    f"{agency_result.content.decode('utf-8')}"
                )

def delete_vehicle(vehicle_device_id):
    vehicle_url = f"{CDF_URL}/devices/{vehicle_device_id}"

    vehicle_result = send_request(
        vehicle_url, "DELETE", AWS_REGION, headers=headers
    )

    if vehicle_result.status_code !=204:
        pytest.fail(
                f"Failed to clean up V2 Vehicle - Response Code -{vehicle_result.status_code}\n"
                f"{vehicle_result.content.decode('utf-8')}"
            )

def delete_com(com_device_id):
    com_url = f"{CDF_URL}/devices/{com_device_id}"

    com_result = send_request(
        com_url, "DELETE", AWS_REGION, headers=headers
    )

    if com_result.status_code !=204:
        pytest.fail(
            f"Failed to clean up Com - Response Code -{com_result.status_code}\n"
            f"{com_result.content.decode('utf-8')}"

        )

def get_API_token():
    """Attempt to retreive the access token from the auth. surver
    fail if this doesn't work for any reason.

    returns - api authorization token
    """

    api_keys = def_get_cognito_auth()
    client_id = api_keys.get("CEIDevAppClientID", None)
    client_secret = api_keys.get("CEIDevAppClientSecret", None)
    api_auth_server = api_keys.get("CEIAuthURL", None)
    api_token_request_call = requests.post(
        f"{api_auth_server}/oauth2/token",
        auth=(client_id, client_secret),
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )

    if 200 != api_token_request_call.status_code:
        pytest.fail(
            f"Unable to retrieve API Token - Response {str(api_token_request_call)} keys - {client_id},{client_secret}"
        )

    return api_token_request_call.json()["access_token"]

def get_API_url():
    api_keys = def_get_cognito_auth()
    return api_keys.get("CEIAPIURL", None)

def run_SQS_confirmation():
    """Confirm if SQS receieved an intended message.
    fail otherwise
    """
    # SQS Set up
    queue = SQS.get_queue_by_name(QueueName="cei-sqs.fifo")
    # confirm SQS Message presence.
    for message in queue.receive_messages(MessageAttributeNames=["messageId"]):
        if message.message_attributes is None:
            pytest.fail("Unable to confirm SqS. No messages in cei-sqs.fifo")
        process_timeout = 10
        while message.message_attributes is not None and process_timeout > 0:
            time.sleep(5)
            process_timeout = process_timeout - 1
        if process_timeout < 1:
            pytest.fail("Unable to process SqS. No messages in cei-sqs.fifo")

def run_dynamo_confirmation(msgId):
    """Confirm a given incident is present within the dynamoDb
        fail if unsuccessful
    Args:
        msgId (string): id of incident message to confirm
    """
    table = DYNAMODB.Table("CEI-IncidentTracking")
    print(f"run_dynamo_confirmation: {msgId}")
    query_response = table.query(ConsistentRead=True,KeyConditionExpression=Key("IncidentID").eq(msgId))
    retry = 10
    while query_response.get("Count") != 1 and retry > 0:
        query_response = table.query(ConsistentRead=True,KeyConditionExpression=Key("IncidentID").eq(msgId))
        retry = retry - 1
        time.sleep(10)
    if query_response.get("Count") != 1:
        pytest.fail(
            f"Failure - unable to confirm incident creation from dynamoDB - {str(query_response)}"
        )
    print(query_response)

def run_priority_confirmation(active, site_id, agency_id, vehicle_id):
    """Confirm the desired active state of a given vehicle

    Args:
        Active (Bool): whether or not the vehicle in question is intended to be active or not
    """
    process_timeout = 10
    print(f"site_id = {site_id}")
    print(f"agency_id = {agency_id}")
    print(f"vehicle_id = {vehicle_id}")
    vehicle_status = get_vehicle_by_all_cei_vals(site_id, agency_id, vehicle_id)
    print(f"vehicle_status ={vehicle_status}")


    #vehicle_status = vehicle_status.get("attributes")
    while vehicle_status["CEIVehicleActive"] is not active and process_timeout > 0:
        print(f'CEIVehicleActive = {vehicle_status["CEIVehicleActive"]}')
        time.sleep(10)
        process_timeout = process_timeout - 1
        vehicle_status = get_vehicle_by_all_cei_vals(site_id, agency_id, vehicle_id)
    if process_timeout < 1:
        pytest.fail(
            f"SQS Message process failed activation check - Vehicle Status = {str(vehicle_status['CEIVehicleActive'])} vs {active}"
        )

def run_API_incident_call(filename, check_activation, activate):

    # API Post data Processing variables
    data = open_json_file(filename, False)
    print(f"filename = {filename}")
    data_call = json.dumps(data).replace("RANDOMIZEGUID", str(uuid.uuid4()))
    api_url = get_API_url()
    # Get API Token
    api_token = get_API_token()
    headers["Authorization"] = api_token
    agency_id = data["agencyId"]
    site_id = data["siteId"]
    print(f"agency_id = {agency_id}")
    # construct API Call
    incident_url = f"{api_url}/cad/incidents"
    incident_post_results = requests.post(incident_url, data=data_call, headers=headers)
    
    #retry to overcome 503 errors...
    retry = 5
    while retry > 0 and 202 != incident_post_results.status_code:
        incident_post_results = requests.post(incident_url, data=data_call, headers=headers)
        retry = retry - 1
        time.sleep(2)
    
    if 202 != incident_post_results.status_code:
        pytest.fail(
            f"API post {incident_url} has failed - response: {str(incident_post_results)}, API Token = {api_token}"
        )
 
    # confirm SQS Message presence.
    run_SQS_confirmation()

    # confirm incident creation
    run_dynamo_confirmation(data["incidents"][0]["id"])

    # confirm vehicle activation.
    if check_activation:
        vehicle_id = data["incidents"][0]["units"][0]["deviceId"]
        incident_id = data["incidents"][0]["id"]
        print(f"vehicle_id = {vehicle_id}")
        run_priority_confirmation(activate, site_id, agency_id, vehicle_id)
        
        # incidentId = data["incidents"][0]["id"]
        # resp = client.query(
        #     TableName='CEI-UnitAssignmentTracking',
        #     IndexName='IncidentID-index',
        #     ExpressionAttributeValues={
        #         ':v1': {
        #             'S': incidentId,
        #         },
        #     },
        #     KeyConditionExpression='IncidentID = :v1',
        # )
        
        # for assignedUnit in resp.get("Items"):
        #     newUnit = {"deviceId": assignedUnit.get("CEIID").get("S")}
        #     print(f"newUnit = {newUnit}") 
        #     run_priority_confirmation(activate, site_id, agency_id, newUnit)

## convert to json data for better output
def convert_json(data):
    return json.dumps(dict(data), indent = 2)

def CDF_clear_all_cache():
    table = DYNAMODB.Table("CEI-CDF-Cache")
    incident_table = DYNAMODB.Table("CEI-IncidentTracking")

    cache_item = {
        "Items": [
            {"CDFID": "cei_ete_com_one"},
            {"CDFID": "cei_ete_com_two"},
            {"CDFID": "cei_ete_com_three"},
        ]
    }

    incident_item = {
        "Items": [
            {"IncidentID": "test_activateSecondIncident"},
            {"IncidentID": "test_SecondAgencyReporting"},
            {"IncidentID": "test_activateV2Vehicle"},
        ]
    }

    with table.batch_writer() as batch:
        for each in cache_item["Items"]:
            batch.delete_item(Key={"CDFID": each["CDFID"]})

    with incident_table.batch_writer() as batch:
        for each in incident_item["Items"]:
            batch.delete_item(Key={"IncidentID": each["IncidentID"]})
    return

def clear_test_data():
    """Add the fixture file data to clear before every test"""
    CDF_clear_all_cache()
    region_one_name = open_json_file('CEIRegion.json', True).get('name')
    CEIagency_one_name = open_json_file('CEIAgency.json', True).get('name') 
    vehicle_one_device_id = open_json_file('CEIVehicleOne.json', True).get('deviceId')
    com_one_device_id = open_json_file('StandardComOne.json', True).get('deviceId')
    
    standard_agency_name = open_json_file('StandardAgency.json', True).get('name')


    CEIagency_two_name = open_json_file('CEIAgencyTwo.json', True).get('name')
    
    vehicle_two_device_id = open_json_file('CEIVehicleTwo.json', True).get('deviceId')
    com_two_device_id = open_json_file('StandardComTwo.json', True).get('deviceId')
    
    vehicle_three_device_id = open_json_file('CEIVehicleThree.json', True).get('deviceId')
    com_three_device_id = open_json_file('StandardComThree.json', True).get('deviceId')

    #Clear Coms
    delete_com(com_one_device_id)
    delete_com(com_two_device_id)
    delete_com(com_three_device_id)

    #Clear Vehicles
    delete_vehicle(vehicle_one_device_id)
    delete_vehicle(vehicle_two_device_id)
    delete_vehicle(vehicle_three_device_id)
    
    #Clear Agencies
    delete_agency(region_one_name, CEIagency_one_name)
    delete_agency(region_one_name, CEIagency_two_name)
    delete_agency(region_one_name, standard_agency_name)
    
    #Clear Region
    delete_region(region_one_name)
