import os
import sys
import json
import boto3
import config_asset_lib
import requests
from requests_aws_sign import AWSV4Sign

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 3 * "/.."), "CDFBackend")
)
from ui import (  # noqa: E402
    del_vehicle,
    del_communicator,
    del_phaseselector,
    del_agency,
    del_region,
    list_agencies,
    list_devices,
)

# Use values from config file
log = config_asset_lib.log
BASE_URL = config_asset_lib.BASE_URL
HEADERS = {
    "Accept": config_asset_lib.ACCEPT,
    "content-type": config_asset_lib.CONTENT_TYPE,
}

# set up authentication
try:
    service = "execute-api"
    credentials = boto3.Session().get_credentials()
    aws_region = os.environ["AWS_REGION"]
    auth = AWSV4Sign(credentials, aws_region, service)
except Exception as e:
    print(f"error: {str(e)}")


def lambda_handler(event, context):
    try:
        print(f"lambda_handler(): event = {event}")
        entity_string = event["body"]
        entity_dict = json.loads(entity_string)
        print(f"lambda_handler(): entity_dict = {entity_dict}")
        rc = False
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
            "body": "Successfully deleted",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

        # if relationship is True, the request is to delete entities' relationship (i.e. Dissociation)
        if entity_dict.get("relationship", "") == "True":
            vehicleName = entity_dict.get("vehicleName")
            selected = entity_dict.get("selected")
            if not selected:
                errorMessage["body"] = "You should select at least one entity"
                return errorMessage
            if len(selected) > 30:
                errorMessage["body"] = "You should select no more than 30 entities"
                return errorMessage

            if vehicleName:
                error = False
                for item in selected:
                    url = f"{BASE_URL}/devices/{item}/installedat/in/devices/{vehicleName}"
                    r = requests.delete(url, headers=HEADERS, auth=auth)
                    print(r)
                    if r.status_code >= 300 or r.status_code < 200:
                        errorMessage["body"] = r.content
                        errorMessage["statusCode"] = r.status_code
                        error = True
                        break
                if error:
                    return errorMessage
                else:
                    successMessage[
                        "body"
                    ] = f"Successfully dissociate {' '.join(selected)} with {vehicleName}"
                    return successMessage
            else:
                errorMessage["body"] = "Invalid input JSON"
                return errorMessage

        # the request is to delete entities
        regions = entity_dict.get("regions")
        agencies = entity_dict.get("agencies")
        vehicles = entity_dict.get("vehicles")
        communicators = entity_dict.get("communicators")
        phase_selectors = entity_dict.get("phase_selectors")
        if all(
            v is None
            for v in [regions, agencies, vehicles, communicators, phase_selectors]
        ):
            errorMessage["body"] = "Error: No entities to delete"
            return errorMessage

        # record entities that failed to delete
        failed_entities = []

        # delete first devices then their agencies and regions
        if communicators:
            for item in communicators:
                region, agency, communicator = item.split("/")
                rc, error = del_communicator(region, agency, None, communicator)
                if not rc:
                    failed_entities.append(f"Communicator {communicator}: {error}")

        if vehicles:
            for item in vehicles:
                region, agency, vehicle = item.split("/")
                print(f"{region},{agency},{vehicle}")
                rc, error = del_vehicle(region, agency, vehicle)
                if not rc:
                    failed_entities.append(f"Vehicle {vehicle}: {error}")

        if phase_selectors:
            for item in phase_selectors:
                region, agency, ps = item.split("/")
                rc, error = del_phaseselector(region, agency, ps)
                if not rc:
                    failed_entities.append(f"Phase selector {ps}: {error}")

        if agencies:
            # check for orphans; delete if none
            for item in agencies:
                region, agency = item.split("/")
                rc, device_list = list_devices(region, agency)
                # rc is False if agency has no children and device_list is empty
                if not device_list:
                    rc, error = del_agency(region, agency)
                    if not rc:
                        failed_entities.append(f"Agency {agency}: {error}")
                else:
                    error = "Agency has children, cannot be deleted until children are removed"
                    failed_entities.append(f"Agency {agency}: {error}")

        if regions:
            # check for orphans; delete if none
            for item in regions:
                region = item.split("/")[0]
                rc, agency_list = list_agencies(region)
                # rc is False if region has no children and agency_list is empty
                if not agency_list:
                    rc, error = del_region(region)
                    if not rc:
                        failed_entities.append(f"Region {region}: {error}")
                else:
                    error = "Region has children, cannot be deleted until children are removed"
                    failed_entities.append(f"Region {region}: {error}")

        if failed_entities:
            errorMessage["body"] = "\n".join(failed_entities)
            return errorMessage
        return successMessage
    except Exception as e:
        print(f"error: {str(e)}")
        errorMessage["body"] = str(e)
        return errorMessage
