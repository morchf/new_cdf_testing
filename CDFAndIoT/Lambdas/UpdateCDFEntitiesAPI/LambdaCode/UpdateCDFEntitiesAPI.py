# UpdateCDFEntitiesApi.py
# Process requests to update the requested entities

import json
import os
import re
import sys
from uuid import uuid4

import boto3
import config_asset_lib
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from ui_helper import (
    check_field_length,
    check_unique_agency,
    check_unique_device,
    get_region_and_agency_name,
    validate_IMEI,
    validate_MAC,
)

DELETE_CACHE_SQS_URL = os.environ["DeleteFromCacheQueueURL"]

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 3 * "/.."), "CDFBackend")
)
# Read constants and environment variables
# local path is different than lambda path
constants_file_lambda_path = "Constants.json"
constants_file_local_path = os.path.join(dir_path, "../../../CDFBackend/Constants.json")
if os.path.exists(constants_file_local_path):
    constants_file = open(constants_file_local_path)
elif os.path.exists(constants_file_lambda_path):
    constants_file = open(constants_file_lambda_path)
else:
    raise Exception("Constants.json file not found in file tree")

constants = json.load(constants_file)
client = boto3.client("ssm")
http = urllib3.PoolManager()

# Use values from config file
log = config_asset_lib.log
BASE_URL = config_asset_lib.BASE_URL
HEADERS = {
    "Accept": config_asset_lib.ACCEPT,
    "content-type": config_asset_lib.CONTENT_TYPE,
}


def send_request(url, method, region_name, params=None, headers=None):
    # fmt: off
    request = AWSRequest(method=method.upper(), url=url, data=params, headers=headers,)
    # fmt: on
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    return URLLib3Session().send(request.prepare())


# Maximum string length for each entity
region_lengths = {"description": 1000, "name": 200}
agency_lengths = {"description": 1000, "name": 200, "city": 200, "state": 20}
vehicle_lengths = {"description": 500, "name": 100, "deviceId": 100, "type": 100}
ps_lengths = {"description": 500, "gttSerial": 50, "deviceId": 50}
comm_lengths = {"description": 500, "gttSerial": 50, "deviceId": 50}


def successMessage(data):
    return {
        "statusCode": 200,
        "body": f"{data}",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def errorMessage(data, statusCode=400):
    return {
        "statusCode": statusCode,
        "body": f"{str(data)}",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def update_entity_relationship(entity_dict):
    message = errorMessage("Invalid input JSON")
    vehicleName = entity_dict.get("vehicleName")
    selected = entity_dict.get("selected")
    if not selected:
        message = errorMessage("You should select at least one entity")
    if len(selected) > 30:
        message = errorMessage("You should select no more than 30 entities")
    if selected and vehicleName:
        for item in selected:
            url = f"{BASE_URL}/devices/{item}/installedat/in/devices/{vehicleName}"
            response = send_request(
                url=url,
                method="PUT",
                region_name=os.environ["AWS_REGION"],
                headers=HEADERS,
            )
            if response.status_code >= 300 or response.status_code < 200:
                message = errorMessage(response.content, response.status_code)
            else:
                message = successMessage(
                    f"Successfully associated {' '.join(selected)} with {vehicleName}"
                )
    return message


def validate_field_length(templateId, entity_dict):
    if templateId == "region":
        check_field_length(region_lengths, entity_dict, templateId)
    elif templateId == "agency":
        check_field_length(agency_lengths, entity_dict, templateId)
    elif templateId == "vehiclev2":
        check_field_length(vehicle_lengths, entity_dict, templateId)
    elif templateId == "communicator":
        check_field_length(comm_lengths, entity_dict, templateId)
    elif templateId == "phaseselector":
        check_field_length(ps_lengths, entity_dict, templateId)


def lambda_handler(event, context):
    try:
        entity_string = event["body"]
        entity_dict = json.loads(entity_string)

        if (entity_dict.get("relationship", "")).lower() == "true":
            return update_entity_relationship(entity_dict)

        deviceId = entity_dict.get("deviceId")
        name = entity_dict.get("name", deviceId)
        templateId = entity_dict.get("templateId")

        message = successMessage(f"{name} successfully updated.")

        validate_field_length(templateId=templateId, entity_dict=entity_dict)

        if templateId.lower() == "region":
            processRequest(f"{BASE_URL}/groups/%2F{name}", entity_dict)
        elif templateId.lower() == "agency":
            if "CMSId" not in json.dumps(entity_dict):
                entity_dict["attributes"]["CMSId"] = entity_dict["attributes"][
                    "agencyID"
                ].upper()
            check_unique_agency(entity_dict)
            CheckCMSId(entity_dict)
            # Need to know region name to create agency
            region = entity_dict.get("parentPath", "").lstrip("/")
            if log:
                print(f"Processing request for region: {region}")
            processRequest(
                f"{BASE_URL}/groups/%2F{region.lower()}%2F{name.lower()}",
                entity_dict,
            )
        elif templateId.lower() == "vehiclev2":
            # Need to know region, agency name to create vehicle
            region, _ = get_region_and_agency_name(entity_dict)
            processRequest(f"{BASE_URL}/devices/{name}", entity_dict)
        elif templateId.lower() == "communicator":
            updated_entities = get_updated_entities(entity_dict, templateId, name)
            uniqueList = [
                "gttSerial",
                "addressMAC",
                "addressWAN",
                "IMEI",
            ]
            if ("model" in updated_entities) and (
                entity_dict["attributes"]["model"] not in ["2100", "2101"]
            ):
                validate_MAC(entity_dict["attributes"]["addressMAC"])
                validate_IMEI(entity_dict["attributes"]["IMEI"])
                if any(
                    x
                    in [
                        "gttSerial",
                        "addressWAN",
                        "addressMAC",
                        "IMEI",
                    ]
                    for x in updated_entities
                ):
                    if entity_dict["attributes"]["model"] in [
                        "2100",
                        "2101",
                    ]:
                        uniqueList = ["gttSerial", "addressWAN"]
                    else:
                        uniqueList = [
                            "gttSerial",
                            "addressMAC",
                            "addressWAN",
                            "IMEI",
                        ]
                    check_unique_device(entity_dict, uniqueList)
            # update communicator
            processRequest(f"{BASE_URL}/devices/{name}", entity_dict)
        elif templateId.lower() == "phaseselector":
            validate_MAC(entity_dict["attributes"]["addressMAC"])
            validate_IMEI(entity_dict["attributes"]["IMEI"])
            uniqueList = [
                "gttSerial",
                "addressMAC",
                "addressLAN",
                "addressWAN",
                "IMEI",
            ]
            check_unique_device(entity_dict, uniqueList)
            processRequest(f"{BASE_URL}/devices/{name}", entity_dict)
        else:
            message = errorMessage("Invalid input JSON")
        return message
    except Exception as e:
        print(f"error: {str(e)}")
        return errorMessage(str(e))


def processRequest(url, entity_dict):
    if log:
        print(
            f"Processing request with payload: \rUrl:{url} \rmethod:PATCH \rparams: {json.dumps(entity_dict)}"
        )
    response = send_request(
        url=url,
        method="PATCH",
        region_name=os.environ["AWS_REGION"],
        params=json.dumps(entity_dict),
        headers=HEADERS,
    )
    if response.status_code == 204:
        push_to_sqs(entity_dict)
    else:
        if log:
            print(
                f"Error for aws request: \rStatusCode: {response.status_code}\rContent:{response.content} \rRaw: {response.raw}"
            )
        raise Exception(errorMessage(response.content, response.status_code))


def CheckCMSId(entity_dict):
    check_guid_regex = (
        "^[{]?[0-9a-fA-F]{8}" + "-([0-9a-fA-F]{4}-)" + "{3}[0-9a-fA-F]{12}[}]?$"
    )  # noqa: E501
    compiled_regex = re.compile(check_guid_regex)
    CMSId = (entity_dict.get("attributes").get("CMSId")).upper()
    if not CMSId:
        CMSId = (entity_dict.get("attributes").get("agencyID")).upper()
    if not re.search(compiled_regex, CMSId):
        raise Exception("CMSId provided is not a valid GUID")


# function to send a message to DeleteFromCacheQueue.fifo SQS queue with entity information as the message body
def push_to_sqs(entity_dict, messageGroupId="DeleteFromCache"):
    sqs_client = boto3.client("sqs", region_name=os.environ["AWS_REGION"])
    messageDeduplicationId = str(uuid4())
    response = sqs_client.send_message(
        QueueUrl=DELETE_CACHE_SQS_URL,
        DelaySeconds=0,
        MessageBody=(f"{json.dumps(entity_dict)}"),
        MessageGroupId=(messageGroupId),
        MessageDeduplicationId=messageDeduplicationId,
    )

    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        return
    else:
        raise Exception(f"Entity could not be deleted from the cache. Error:{response}")


# function to return changed fields when updating
def get_updated_entities(entity_dict, templateId, name):
    url = f"{BASE_URL}/devices/{name}"
    response = send_request(
        url=url,
        method="GET",
        region_name=os.environ["AWS_REGION"],
        params=json.dumps(entity_dict),
        headers=HEADERS,
    )
    if response.status_code == 200:
        entity_list = [
            "gttSerial",
            "serial",
            "make",
            "model",
            "addressLAN",
            "addressWAN",
            "description",
            "IMEI",
            "addressMAC",
        ]

        current_deviceId = entity_dict.get("deviceId")
        updated_entities = []
        device = json.loads(response.content)
        tmp_deviceId = device.get("deviceId")
        tmp_templateId = device.get("templateId")
        if (tmp_deviceId == current_deviceId) and (tmp_templateId == templateId):
            for entity in entity_list:
                res = compare_entities(entity, entity_dict, device)
                if not res:
                    updated_entities.append(entity)
            return updated_entities
    else:
        raise Exception(errorMessage(response.content, response.status_code))
    return []


def compare_entities(entity_name, source_dict, temp_dict):
    rc = True
    if entity_name == "description":
        if temp_dict[entity_name] != source_dict[entity_name]:
            rc = False
    elif temp_dict["attributes"][entity_name] != source_dict["attributes"][entity_name]:
        rc = False
    return rc
