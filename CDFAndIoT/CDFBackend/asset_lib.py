#!/usr/bin/env python
import os
import boto3
import json
import config_asset_lib
import requests
from requests_aws_sign import AWSV4Sign

# Use values from config file
log = config_asset_lib.log
BASE_URL = config_asset_lib.BASE_URL
HEADERS = {
    "Accept": config_asset_lib.ACCEPT,
    "content-type": config_asset_lib.CONTENT_TYPE,
}

# set up authentication
service = "execute-api"
credentials = boto3.Session().get_credentials()
aws_region = os.environ["AWS_REGION"]
auth = AWSV4Sign(credentials, aws_region, service)


def region_create(region_name, region_json_str):
    # Notes:
    #   1. The "name" in the region_json_str must match region_name
    #   2. The "TemplateId" in the region_json_str must be "region" to map
    #      to region_template.json
    #   3. The "parentPath" in the region_json_str must be "/region" to define
    #      root as the parent of this group
    region_name = region_name.lower()

    if log:
        print(f"****** creating region = {region_name} *****")

    url = BASE_URL + "/groups"
    r = requests.post(url, headers=HEADERS, data=region_json_str, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def region_read(region_name):
    region_name = region_name.lower()

    if log:
        print(f"****** region read = {region_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def region_write(region_name, write_json_str):
    region_name = region_name.lower()

    if log:
        print(f"****** region write = {region_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}"
    r = requests.patch(url, headers=HEADERS, data=write_json_str, auth=auth)
    if log:
        print(f"patch response = {r.status_code}")
        print(f"patch request headers = {r.request.headers}")
        print(f"patch request body = {r.request.body}")

    return r.status_code, r.content


def region_delete(region_name):
    region_name = region_name.lower()

    if log:
        print(f"****** deleting region = {region_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}"
    r = requests.delete(url, headers=HEADERS, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def list_all_regions():
    if log:
        print("****** list all regions *****")

    url = BASE_URL + "/groups/%2F/members/groups"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def agency_create(agency_name, agency_json_str):
    # Notes:
    #   1. The "name" in the agency_json_str must match agency_name
    #   2. The "TemplateId" in the agency_json_str must be "agency" to map
    #      to agency_template.json
    #   3. The "parentPath" in the agency_json_str must be "/agency" to define
    #      root as the parent of this group
    agency_name = agency_name.lower()

    if log:
        print(f"****** creating agency = {agency_name} *****")

    url = BASE_URL + "/groups"
    r = requests.post(url, headers=HEADERS, data=agency_json_str, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def agency_read(region_name, agency_name):
    agency_name = agency_name.lower()

    if log:
        print("****** agency read = {} *****".format(agency_name))

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def agency_write(region_name, agency_name, write_json_str):
    agency_name = agency_name.lower()

    if log:
        print("****** agency write = {} *****".format(agency_name))

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}"
    r = requests.patch(url, headers=HEADERS, data=write_json_str, auth=auth)
    if log:
        print(f"patch response = {r.status_code}")
        print(f"patch request headers = {r.request.headers}")
        print(f"patch request body = {r.request.body}")

    return r.status_code, r.content


def agency_delete(region_name, agency_name):
    agency_name = agency_name.lower()
    region_name = region_name.lower()

    if log:
        print(f"****** deleting agency = {agency_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}"
    r = requests.delete(url, headers=HEADERS, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def list_all_devices_in_agency(region_name, agency_name):
    agency_name = agency_name.lower()

    if log:
        print(f"****** list all devices in the agency = {agency_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}/members/devices"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def list_all_vehicles_in_agency(region_name, agency_name):
    agency_name = agency_name.lower()

    if log:
        print(f"****** list all vehicles in the agency = {agency_name} *****")

    url = (
        BASE_URL
        + f"/groups/%2F{region_name}%2F{agency_name}/ownedby/devices?template=vehiclev2"
    )
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def list_all_agencies_in_region(region_name):
    if log:
        print(f"****** list all agencies in the region = {region_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}/members/groups"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def device_create(device_json_str):
    # Notes:
    # 1. The "deviceId" in the device_json_str is the device name
    # 2. The "TemplateId" in the device_json_str must be "phaseselector" to create
    #    a device with the phaseselector_template.json. Alternately, if an other
    #    device template is desired, the template for that other device
    #    must be identified (e.g. traffic for traffic_template.json).
    # 3. The device json must define the relationship to the agency.
    #    Json snippet showing relationship between device and agency:
    #    "groups": {
    #       "in": {
    #           "owns": ["/r1/a1"]
    #       }
    #    }
    if log:
        device_json_obj = json.loads(device_json_str)
        device_name = device_json_obj.get("deviceId", None)
        print(f"****** creating device = {device_name} *****")
    url = BASE_URL + "/devices"
    r = requests.post(url, headers=HEADERS, data=device_json_str, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def device_read(device_name):
    if log:
        print(f"****** read device = {device_name} *****")

    url = BASE_URL + f"/devices/{device_name}"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get request content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def device_write(device_name, write_json_str):
    if log:
        print(f"****** device write = {device_name} *****")

    url = BASE_URL + f"/devices/{device_name}"
    r = requests.patch(url, headers=HEADERS, data=write_json_str, auth=auth)
    if log:
        print(f"patch response = {r.status_code}")
        print(f"patch request headers = {r.request.headers}")
        print(f"patch request body = {r.request.body}")

    return r.status_code, r.content


def device_delete(device_name):
    if log:
        print(f"****** deleting device = {device_name} *****")

    url = BASE_URL + f"/devices/{device_name}"
    r = requests.delete(url, headers=HEADERS, auth=auth)
    if log:
        print(f"delete response = {r.status_code}")
        print(f"delete request headers = {r.request.headers}")
        print(f"delete request body = {r.request.body}")

    return r.status_code, r.content


def list_all_communicators_in_vehicle(vehicle_name):
    if log:
        print(f"****** list all communicators in the vehicle = {vehicle_name} *****")

    url = BASE_URL + f"/devices/{vehicle_name}/installedat/devices"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def communicator_associate(communicator_name, vehicle_name):
    if log:
        print(
            f"****** associating communicator = {communicator_name} to vehicle = {vehicle_name} *****"
        )

    url = (
        BASE_URL
        + f"/devices/{vehicle_name}/installedat/out/devices/{communicator_name}"
    )
    r = requests.put(url, headers=HEADERS, auth=auth)
    if log:
        print(f"put response = {r.status_code}")
        print(f"put request headers = {r.request.headers}")
        print(f"put request body = {r.request.body}")

    return r.status_code, r.content


def communicator_disociate(communicator_name, vehicle_name):
    if log:
        print(
            f"****** dissociating communicator = {communicator_name} to vehicle = {vehicle_name} *****"
        )

    url = (
        BASE_URL
        + f"/devices/{vehicle_name}/installedat/out/devices/{communicator_name}"
    )
    r = requests.delete(url, headers=HEADERS, auth=auth)
    if log:
        print(f"delete response = {r.status_code}")
        print(f"delete request headers = {r.request.headers}")
        print(f"delete request body = {r.request.body}")

    return r.status_code, r.content


def location_create(location_name, location_json_str):
    # Notes:
    #   1. The "location_id" in the location_json_str must match location_name
    #   2. The "TemplateId" in the location_json_str must be "location" to map
    #      to location_template.json

    if log:
        print(f"****** creating location = {location_name} *****")

    url = BASE_URL + "/groups"
    r = requests.post(url, headers=HEADERS, data=location_json_str, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def location_read(region_name, agency_name, location_name):
    agency_name = agency_name.lower()
    region_name = region_name.lower()
    location_name = location_name.lower()

    if log:
        print(f"****** location read = {location_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}%2F{location_name}"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content


def location_write(region_name, agency_name, location_name, write_json_str):
    agency_name = agency_name.lower()
    region_name = region_name.lower()
    location_name = location_name.lower()

    if log:
        print(f"****** location write = {location_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}%2F{location_name}"
    r = requests.patch(url, headers=HEADERS, data=write_json_str, auth=auth)
    if log:
        print(f"patch response = {r.status_code}")
        print(f"patch request headers = {r.request.headers}")
        print(f"patch request body = {r.request.body}")

    return r.status_code, r.content


def location_delete(region_name, agency_name, location_name):
    agency_name = agency_name.lower()
    region_name = region_name.lower()
    location_name = location_name.lower()

    if log:
        print(f"****** deleting location = {location_name} *****")

    url = BASE_URL + f"/groups/%2F{region_name}%2F{agency_name}%2F{location_name}"
    r = requests.delete(url, headers=HEADERS, auth=auth)
    if log:
        print(f"post response = {r.status_code}")
        print(f"post request headers = {r.request.headers}")
        print(f"port request body = {r.request.body}")

    return r.status_code, r.content


def list_all_locations():
    if log:
        print("****** list all locations *****")

    url = BASE_URL + "/groups/%2F/members/groups"
    r = requests.get(url, headers=HEADERS, auth=auth)
    if log:
        print(f"get response = {r.status_code}")
        print(f"get response content = {r.content}")
        print(f"get request headers = {r.request.headers}")
        print(f"get request body = {r.request.body}")

    return r.status_code, r.content
