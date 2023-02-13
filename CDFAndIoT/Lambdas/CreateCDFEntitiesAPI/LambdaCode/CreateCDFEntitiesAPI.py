import json
import urllib3
from urllib.parse import urlencode
import uuid
import os
import boto3
import sys

from services.queue_job import Client as QueueJob

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

from ui import (
    new_region,
    new_agency,
    new_vehicle,
    new_communicator,
    new_phaseselector,
)
from ui_helper import (
    check_field_length,
    validate_IMEI,
    validate_MAC,
    check_unique_agency,
    check_unique_device,
    get_region_and_agency_name,
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

aws_account = boto3.client("sts").get_caller_identity().get("Account")
aws_region = os.environ["AWS_REGION"]

constants = json.load(constants_file)
client = boto3.client("ssm")
queue_job = QueueJob(aws_account, aws_region)
http = urllib3.PoolManager()
os.environ["OAUTH_URL"] = constants["OAUTH_URL"]
os.environ["GET_URL"] = constants["GET_URL"]

# Maximum string length for each entity
region_lengths = {"description": 1000, "name": 200}
agency_lengths = {"description": 1000, "name": 200, "city": 200, "state": 20}
vehicle_lengths = {"description": 500, "name": 100, "deviceId": 100, "type": 100}
ps_lengths = {"description": 500, "gttSerial": 50, "deviceId": 50}
comm_lengths = {"description": 500, "gttSerial": 50, "deviceId": 50}


def get_modem_data(serialNumber):
    data = None
    access_token = None
    URL = None
    r = None

    try:
        username = client.get_parameter(Name="SW-API-username", WithDecryption=True)
        password = client.get_parameter(Name="SW-API-password", WithDecryption=True)
        client_id = client.get_parameter(Name="SW-API-client-ID", WithDecryption=True)
        client_secret = client.get_parameter(
            Name="SW-API-client-secret", WithDecryption=True
        )
        company = client.get_parameter(
            Name="SW-API-GTT-Company-Number", WithDecryption=True
        )
    except Exception as e:
        print(f"get_modem_data() error: {str(e)}")

    try:
        encoded_args = urlencode(
            {
                "grant_type": "password",
                "username": username["Parameter"]["Value"],
                "password": password["Parameter"]["Value"],
                "client_id": client_id["Parameter"]["Value"],
                "client_secret": client_secret["Parameter"]["Value"],
            }
        )
    except Exception as e:
        print(f"get_modem_data() error: {str(e)}")

    # Request token
    try:
        URL = os.environ["OAUTH_URL"] + encoded_args
        r = http.request("POST", URL)
        if r:
            response = json.loads(r.data)
            access_token = response["access_token"]
            print(access_token)
    except Exception as e:
        print(f"get_modem_data() error: {str(e)}")

    # Get Modem data
    try:
        URL = f"{os.environ['GET_URL']}{company['Parameter']['Value']}&gateway=serialNumber:{serialNumber}&access_token={access_token}"  # noqa: E501
        if r:
            modem_data = json.loads(r.data)
            data = modem_data.get("items")
    except Exception as e:
        print(f"get_modem_data() error: {str(e)}")

    return data


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


def create_entity(entity_dict):

    deviceId = entity_dict.get("deviceId")
    templateId = entity_dict.get("templateId")
    if templateId == "vehiclev2" and (
        not deviceId or deviceId == "" or deviceId == "NULL_GUID"
    ):
        guid_str = str(uuid.uuid1()).upper()
        entity_dict["deviceId"] = guid_str
        name = guid_str
    else:
        name = entity_dict.get("name", deviceId)

    if templateId == "communicator":
        vehicle = entity_dict.pop("vehicle")
        # Need to convert from int to string if IMEI is extracted from XLSX file
        imei = entity_dict.get("attributes", {}).get("IMEI", "")
        entity_dict["attributes"]["IMEI"] = str(imei)
    # save to /tmp directory
    fp = f"/tmp/{name}.json"
    with open(fp, "w") as file:
        json.dump(entity_dict, file)
    file.close()

    errorMessage = {
        "statusCode": 400,
        "body": "",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
    successMessage = {
        "statusCode": 200,
        "body": name + " successfully created!",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }

    try:
        validate_field_length(templateId=templateId, entity_dict=entity_dict)

        # create new region
        if templateId == "region":
            rc, error = new_region(name)
            if not rc:
                os.remove(fp)
                errorMessage["body"] = str(error)
                print(errorMessage)
                return False, errorMessage
            os.remove(fp)
            return True, successMessage

        elif templateId == "agency":
            # Check attribute values are unique among regions and agencies
            check_unique_agency(entity_dict)
            # Need to know region name to create agency
            region = entity_dict.get("parentPath", "").lstrip("/")
            rc, error = new_agency(region, name)
            if not rc:
                os.remove(fp)
                errorMessage["body"] = str(error)
                return False, errorMessage
            os.remove(fp)
            return True, successMessage

        elif templateId == "vehiclev2":
            # Need to know region, agency name to create vehicle
            region, agency = get_region_and_agency_name(entity_dict)
            rc, error = new_vehicle(region, agency, name)
            if not rc:
                os.remove(fp)
                if "already exists. No changes made" in error:
                    error = f"Error: Device ID {name} already exists"
                errorMessage["body"] = str(error)
                return False, errorMessage
            os.remove(fp)
            return True, successMessage

        elif templateId == "communicator":
            # Replace addressMAC, addressWAN, IMEI if model is "MP-70"
            if entity_dict["attributes"]["model"] == "MP-70":
                get_data = get_modem_data(entity_dict["deviceId"])
                if get_data is not None and get_data != []:
                    print(get_data[0])
                    entity_dict["attributes"]["addressMAC"] = get_data[0]["gateway"][
                        "macAddress"
                    ]
                    entity_dict["attributes"]["addressWAN"] = get_data[0][
                        "subscription"
                    ]["ipAddress"]
                    entity_dict["attributes"]["IMEI"] = get_data[0]["gateway"]["imei"]
            # Check MAC, IMEI validation if model is not "2100" or "2101"
            if entity_dict["attributes"]["model"] not in ["2100", "2101"]:
                validate_MAC(entity_dict["attributes"]["addressMAC"])
                validate_IMEI(entity_dict["attributes"]["IMEI"])

            # Check Uniqueness
            if entity_dict["attributes"]["model"] in ["2100", "2101"]:
                uniqueList = ["gttSerial", "addressWAN"]
            else:
                uniqueList = ["gttSerial", "addressMAC", "addressWAN", "IMEI"]
            check_unique_device(entity_dict, uniqueList)

            # Need to know region, agency, vehicle(optional) name to create communicator
            region, agency = get_region_and_agency_name(entity_dict)
            if vehicle == "":
                vehicle = None
            rc, error = new_communicator(region, agency, vehicle, name)
            if not rc:
                os.remove(fp)
                if "already exists. No changes made" in error:
                    error = f"Error: Device ID {name} already exists"
                errorMessage["body"] = str(error)
                return False, errorMessage
            os.remove(fp)
            return True, successMessage

        elif templateId == "phaseselector":
            # Replace addressMAC, addressWAN, IMEI if model is "MP-70"
            if entity_dict["attributes"]["model"] == "MP-70":
                get_data = get_modem_data(entity_dict["deviceId"])
                if get_data is not None and get_data != []:
                    print(get_data[0])
                    entity_dict["attributes"]["addressMAC"] = get_data[0]["gateway"][
                        "macAddress"
                    ]
                    entity_dict["attributes"]["addressWAN"] = get_data[0][
                        "subscription"
                    ]["ipAddress"]
                    entity_dict["attributes"]["IMEI"] = get_data[0]["gateway"]["imei"]
            validate_MAC(entity_dict["attributes"]["addressMAC"])
            validate_IMEI(entity_dict["attributes"]["IMEI"])
            # Check Uniqueness
            uniqueList = ["gttSerial", "addressMAC", "addressLAN", "addressWAN", "IMEI"]
            check_unique_device(entity_dict, uniqueList)

            # Need to know region, agency name to create phaseselector
            region, agency = get_region_and_agency_name(entity_dict)
            rc, error = new_phaseselector(region, agency, name)
            if not rc:
                os.remove(fp)
                if "already exists. No changes made" in error:
                    error = f"Error: Device ID {name} already exists"
                errorMessage["body"] = str(error)
                return False, errorMessage
            os.remove(fp)
            return True, successMessage
        else:
            raise Exception("Invalid input JSON")
    except Exception as error:
        os.remove(fp)
        errorMessage["body"] = str(error)
        return False, errorMessage


def lambda_handler(event, context):

    records = event.get("Records")
    if records:
        error_queue_url = queue_job.error_url(
            queue_job.from_topic_arn(records[0]["eventSourceARN"])
        )
        error_messages = []
        for record in records:
            try:
                body = json.loads(record.get("body"))
                entity_dict = json.loads(body)
                res, message = create_entity(entity_dict)

                if not res:
                    error_messages.append({"entity": body, "error": message["body"]})

            except Exception as e:
                print(f"error: {str(e)}")
                error_messages.append({"entity": body, "error": str(e)})

        print("error_messages", error_messages)
        if error_messages:
            res = queue_job.send(QueueUrl=error_queue_url, Messages=error_messages)

    else:
        entity_string = event["body"]
        entity_dict = json.loads(entity_string)
        res, message = create_entity(entity_dict)
        return message
