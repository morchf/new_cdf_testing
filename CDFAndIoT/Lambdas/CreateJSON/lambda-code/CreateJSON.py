import json
import urllib3
from urllib.parse import urlencode
import os
import boto3
import sys
import re
import uuid
import requests

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)
from ui_helper import (
    check_unique_agency,
    check_unique_vehicle,
    check_unique_device,
)
from ui import list_vehicles

# read constants and environment variables
# local path is different than lambda path
# constants_file_local_path = "Constants.json"
# if os.path.exists(constants_file_local_path):
#     constants_file = open(constants_file_local_path)
# else:
#     raise Exception("Constants.json file not found in file tree")
constants_file_local_path = "Constants.json"
constants_file_lambda_path = os.path.join(
    os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend/Constants.json"
)
if os.path.exists(constants_file_local_path):
    constants_file = open(constants_file_local_path)
elif os.path.exists(constants_file_lambda_path):
    constants_file = open(constants_file_lambda_path)
else:
    raise Exception("Constants.json file not found in file tree")

constants = json.load(constants_file)

client = boto3.client("ssm")
http = urllib3.PoolManager()
os.environ["OAUTH_URL"] = constants["OAUTH_URL"]
os.environ["GET_URL"] = constants["GET_URL"]

# Maximum string length for each entity
region_lengths = {"description": 1000, "name": 200}
agency_lengths = {"description": 1000, "name": 200, "city": 200, "state": 20}
vehicle_lengths = {"description": 500, "name": 100, "type": 100}
ps_lengths = {"description": 500, "gttSerial": 50, "deviceId": 50}
comm_lengths = {"description": 500, "gttSerial": 50, "deviceId": 50}
location_lengths = {
    "description": 1000,
    "address": 200,
    "displayName": 200,
    "name": 200,
}


def open_json_file(file_name):
    json_str = None
    json_obj = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        # json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
        json_obj = json.loads(json_str)
    else:
        print(f"{file_name} not found.")

    return json_obj


def validate_IMEI(imei):
    if not re.match("[0-9]{15}$", imei):
        raise Exception("IMEI is not valid")


def validate_MAC(mac_address):
    if not re.match(
        "[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address.lower()
    ):
        raise Exception("MAC address is not valid")


def validate_IP(address):
    if address.count(".") != 3:
        raise Exception("IP address {} is not valid".format(address))
    for part in address.split("."):
        try:
            int(part)
            if int(part) < 0 or int(part) > 255:
                raise Exception("IP address {} is not valid".format(address))
        except:
            raise Exception("IP address {} is not valid".format(address))


def check_field_length(length_dict, data_dict):
    for item in length_dict:
        if item in data_dict:
            data_length = len(data_dict[item])
            allowed_length = length_dict[item]
            if data_length > allowed_length:
                raise Exception(
                    f"The field {item} is {data_length} characters it must be"
                    f" less than {allowed_length} charactor(s)"
                )


def lambda_handler(event, context):
    # zip lists together into dict
    header = event["taskResult-consume-csv"]["header"]
    content = event["taskResult-consume-csv"]["row_content"]

    if header and content:
        entity_dict = dict(zip(header, content))
    else:
        entity_dict = None

    # first item in header or row is the entity type
    # make sure they match before creating JSON file
    if entity_dict.get("region") == "region":
        # verify lengths; if too long throw exception with error message
        check_field_length(region_lengths, entity_dict)

        with open(f"{dir_path}/skeleton_region.json", "r") as file:
            data = json.load(file)

        data["attributes"]["description"] = entity_dict["description"]
        data["name"] = entity_dict["name"]
        if "displayName" in entity_dict:
            data["attributes"]["displayName"] = entity_dict["displayName"]
        data["groupPath"] = f'/{entity_dict["name"]}'

    elif entity_dict.get("agency") == "agency":
        # verify lengths; if too long throw exception with error message
        check_field_length(agency_lengths, entity_dict)

        with open(f"{dir_path}/skeleton_agency.json", "r") as file:
            data = json.load(file)

        data["attributes"]["description"] = entity_dict["description"]
        data["name"] = entity_dict["name"]
        data["attributes"]["city"] = entity_dict["city"]
        data["attributes"]["state"] = entity_dict["state"]
        data["attributes"]["timezone"] = entity_dict["timezone"]
        data["attributes"]["agencyCode"] = int(entity_dict["agencyCode"])
        data["attributes"]["priority"] = entity_dict["priority"]
        if "CMSId" in entity_dict:
            data["attributes"]["CMSId"] = entity_dict["CMSId"]
        if "displayName" in entity_dict:
            data["attributes"]["displayName"] = entity_dict["displayName"]
        data["parentPath"] = f'/{entity_dict["region"]}'
        data["groupPath"] = f'/{entity_dict["region"]}/{entity_dict["name"]}'

        # check agencyCode uniqueness
        try:
            check_unique_agency(data)
        except Exception as error:
            raise Exception(f"{error}")

    elif entity_dict.get("vehicleV2") == "vehicleV2":
        # verify lengths; if too long throw exception with error message
        check_field_length(vehicle_lengths, entity_dict)

        with open(f"{dir_path}/skeleton_vehicleV2.json", "r") as file:
            data = json.load(file)

        # deviceId is a GUID and name is its display name
        data["deviceId"] = str(uuid.uuid1())
        data["attributes"]["name"] = entity_dict["name"]
        data["attributes"]["description"] = entity_dict["description"]
        data["attributes"]["type"] = entity_dict["type"]
        data["attributes"]["class"] = int(entity_dict["class"])
        data["attributes"]["priority"] = entity_dict["priority"]
        data["attributes"]["VID"] = int(entity_dict["VID"])
        data["groups"]["ownedby"][
            0
        ] = f'/{entity_dict["region"]}/{entity_dict["agency"]}'

        # name must be unique within its agency
        try:
            check_unique_vehicle(data)
        except Exception as error:
            raise Exception(f"{error}")

    elif entity_dict.get("communicator") == "communicator":
        # verify lengths; if too long throw exception with error message
        check_field_length(comm_lengths, entity_dict)

        with open(f"{dir_path}/skeleton_comm.json", "r") as file:
            data = json.load(file)

        get_data = get_modem_data(entity_dict["deviceId"])
        MP_70_data = determine_MP70_data(entity_dict, get_data)

        if entity_dict["model"] not in ["2100", "2101"]:
            validate_MAC(MP_70_data[0])
            validate_IMEI(MP_70_data[2])
            data["attributes"]["addressMAC"] = MP_70_data[0]
            data["attributes"]["IMEI"] = MP_70_data[2]

        data["attributes"]["description"] = entity_dict["description"]
        data["attributes"]["serial"] = entity_dict["deviceId"]
        data["attributes"]["gttSerial"] = entity_dict["gttSerial"]
        validate_IP(entity_dict["addressWAN"])
        data["attributes"]["addressWAN"] = MP_70_data[1]
        validate_IP(entity_dict["addressLAN"])
        data["attributes"]["addressLAN"] = entity_dict["addressLAN"]
        data["attributes"]["make"] = entity_dict["make"]
        data["attributes"]["model"] = entity_dict["model"]
        data["groups"]["ownedby"][
            0
        ] = f'/{entity_dict["region"]}/{entity_dict["agency"]}'
        data["deviceId"] = entity_dict["deviceId"]

        # get vehicle's deviceId given its name
        veh_name = entity_dict.get("vehicle", "")
        veh_deviceId = ""
        if veh_name != "":
            _, vehicle_list = list_vehicles(
                entity_dict["region"], entity_dict["agency"]
            )
            for vehicle in vehicle_list:
                if veh_name == vehicle["attributes"]["name"]:
                    veh_deviceId = vehicle.get("deviceId", "")
                    break
            else:
                raise Exception(
                    f"Vehicle {veh_name} does not exist to install {data['deviceId']}"
                )

        # pass the vehicle name to PopulateCDF lambda,
        # will delete it from commu json in PopulateCDF before POST to the assetlib
        data["vehicle"] = veh_deviceId

        # check uniqueness
        try:
            if entity_dict["model"] in ["2100", "2101"]:
                uniqueList = ["gttSerial"]
                check_unique_device(data, uniqueList)
            else:
                uniqueList = ["gttSerial", "addressMAC", "IMEI"]
                check_unique_device(data, uniqueList)
        except Exception as error:
            raise Exception(f"{error}")

    elif entity_dict.get("phaseselector") == "phaseselector":
        # verify lengths; if too long throw exception with error message
        check_field_length(ps_lengths, entity_dict)

        with open(f"{dir_path}/skeleton_ps.json", "r") as file:
            data = json.load(file)

        if entity_dict["addressMAC"]:
            validate_MAC(entity_dict["addressMAC"])

        data["deviceId"] = entity_dict["deviceId"]
        data["attributes"]["gttSerial"] = entity_dict["deviceId"]
        if "description" in entity_dict:
            data["attributes"]["description"] = entity_dict["description"]
        if "addressMAC" in entity_dict:
            data["attributes"]["addressMAC"] = entity_dict["addressMAC"]
        if "addressWAN" in entity_dict:
            validate_IP(entity_dict["addressWAN"])
            data["attributes"]["addressWAN"] = entity_dict["addressWAN"]
        if "addressLAN" in entity_dict:
            validate_IP(entity_dict["addressLAN"])
            data["attributes"]["addressLAN"] = entity_dict["addressLAN"]
        data["attributes"]["make"] = entity_dict["make"]
        data["attributes"]["model"] = entity_dict["model"]
        data["groups"]["ownedby"][
            0
        ] = f'/{entity_dict["region"]}/{entity_dict["agency"]}'

        # check uniqueness
        uniqueList = ["gttSerial", "addressMAC"]
        try:
            check_unique_device(data, uniqueList)
        except Exception as error:
            raise Exception(f"{error}")

    elif entity_dict.get("location") == "location":
        # verify lengths; if too long throw exception with error message
        check_field_length(location_lengths, entity_dict)

        with open(f"{dir_path}/skeleton_location.json", "r") as file:
            data = json.load(file)

        data["attributes"]["description"] = entity_dict["description"]
        data["attributes"]["address"] = entity_dict["address"]
        data["attributes"]["latitude"] = entity_dict["latitude"]
        data["attributes"]["longitude"] = entity_dict["longitude"]
        data["attributes"]["locationId"] = str(uuid.uuid1()).lower()
        data["name"] = data["attributes"]["locationId"]
        if "displayName" in entity_dict:
            data["attributes"]["displayName"] = entity_dict["displayName"]
        if "name" in entity_dict:
            data["attributes"]["displayName"] = entity_dict["name"]
        data["parentPath"] = f'/{entity_dict["region"]}/{entity_dict["agency"]}'
        data[
            "groupPath"
        ] = f'/{entity_dict["region"]}/{entity_dict["agency"]}/{data["attributes"]["locationId"]}'

    else:
        raise Exception("Error invalid input data.")

    return {"entity_json": data}


def determine_MP70_data(entity_dict, get_data):
    device_data = [None] * 3

    if entity_dict["model"] == "MP-70":
        if get_data != None and get_data != []:  # noqa: E711
            print(get_data[0])
            device_data[0] = get_data[0]["gateway"]["macAddress"]
            device_data[1] = get_data[0]["subscription"]["ipAddress"]
            device_data[2] = get_data[0]["gateway"]["imei"]
        else:
            device_data[0] = entity_dict["addressMAC"]
            device_data[1] = entity_dict["addressWAN"]
            device_data[2] = entity_dict["IMEI"]
    elif entity_dict["model"] in ["2100", "2101"]:
        device_data[0] = entity_dict.get("addressMAC", "")
        device_data[1] = entity_dict["addressWAN"]
        device_data[2] = entity_dict.get("IMEI", "")
    else:
        device_data[0] = entity_dict["addressMAC"]
        device_data[1] = entity_dict["addressWAN"]
        device_data[2] = entity_dict["IMEI"]
    print(device_data)
    return device_data


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
        print(f"error: {str(e)}")

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
        print(f"error: {str(e)}")

    # Request token
    try:
        URL = os.environ["OAUTH_URL"] + encoded_args
        r = requests.post(URL)
        if r:
            response = r.json()
            access_token = response["access_token"]
    except Exception as e:
        print(f"error: {str(e)}")

    # Get Modem data
    try:
        URL = f"{os.environ['GET_URL']}{company['Parameter']['Value']}&gateway=serialNumber:{serialNumber}&access_token={access_token}"  # noqa: E501
        r = requests.get(URL)
        if r:
            modem_data = r.json()
            print(modem_data)
            data = modem_data.get("items")
    except Exception as e:
        print(f"error: {str(e)}")

    return data
