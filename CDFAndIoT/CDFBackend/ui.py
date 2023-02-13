import json
import uuid
import argparse
import os
import re
from region import Region
from agency import Agency
from vehicle import Vehicle
from communicator import Communicator
from phaseselector import Phaseselector
from location import Location
import asset_lib as alib
from status import (
    REGION_STATUS_EXISTS,
    REGION_STATUS_DOES_NOT_EXIST,
    AGENCY_STATUS_EXISTS,
    AGENCY_STATUS_DOES_NOT_EXIST,
    DEVICE_STATUS_EXISTS,
    DEVICE_STATUS_DOES_NOT_EXIST,
    DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB,
    LOCATION_STATUS_EXISTS,
    LOCATION_STATUS_DOES_NOT_EXIST,
)

logs = False
err_ok = "Ok, have a nice day."


def get_json(name):
    json_str = None
    file_name = f"/tmp/{name}.json"
    if os.path.exists(file_name):
        with open(file_name) as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "")
        f.close()
    return json_str


def construct_error_message(status, code, content, entity_name):
    str_err = f"Error: {code}, {content}. {entity_name} create status is {status}"
    return str_err


def new_region(region_name):
    rc = False
    error = None
    region_json_str = get_json(region_name)
    if region_json_str:
        if "NULL_GUID" in region_json_str:
            guid_str = str(uuid.uuid1()).upper()
            region_json_str = region_json_str.replace("NULL_GUID", guid_str)
            # if displayName is not given populate it with "name"
            region_json = json.loads(region_json_str)
            if "displayName" not in region_json_str:
                region_json["attributes"]["displayName"] = region_json["name"]
            elif region_json["attributes"]["displayName"] == "":
                region_json["attributes"]["displayName"] = region_json["name"]
            region_json_str = json.dumps(region_json)
            region = Region(region_name)
            if region.status == REGION_STATUS_DOES_NOT_EXIST:
                region.create(region_json_str)
                if region.status == REGION_STATUS_EXISTS:
                    rc = True
                    error = err_ok
                else:
                    rc = False
                    error = construct_error_message(
                        region.status,
                        region.http_code,
                        region.http_content,
                        region_name,
                    )
            else:
                error = (
                    f"Region {region_name} already exists with status "
                    f"= {region.status}, no changes made"
                )
        else:
            error = f"Missing NULL_GUID in {region_name}.json file"
    else:
        error = f"Missing {region_name}.json file"
    return rc, error


def new_agency(region_name, agency_name):
    rc = False
    error = None
    agency_json_str = get_json(agency_name)
    check_guid_regex = (
        "^[{]?[0-9a-fA-F]{8}" + "-([0-9a-fA-F]{4}-)" + "{3}[0-9a-fA-F]{12}[}]?$"
    )  # noqa: E501
    compiled_regex = re.compile(check_guid_regex)
    if agency_json_str:
        if "NULL_GUID" in agency_json_str:
            guid_str = str(uuid.uuid1()).upper()
            agency_json_str = agency_json_str.replace("NULL_GUID", guid_str)
            agency_json = json.loads(agency_json_str)
            if (
                "CMSId" not in agency_json_str
                or agency_json["attributes"]["CMSId"] == ""
            ):
                # agency ID and CMS ID should be different so create a new guid if cms id is not present
                agency_json["attributes"]["CMSId"] = str(uuid.uuid1()).upper()
            # check if guid provided is valid
            elif not re.search(compiled_regex, agency_json["attributes"]["CMSId"]):
                rc = False
                error = "CMSId provided is not a valid GUID"
                return rc, error
            else:
                agency_json["attributes"]["CMSId"] = agency_json["attributes"][
                    "CMSId"
                ].upper()  # noqa: E501
            # if displayName is not given populate it with "name"
            if "displayName" not in agency_json_str:
                agency_json["attributes"]["displayName"] = agency_json["name"]
            elif agency_json["attributes"]["displayName"] == "":
                agency_json["attributes"]["displayName"] = agency_json["name"]
            agency_json_str = json.dumps(agency_json)
            agency = Agency(region_name, agency_name)
            if agency.status == AGENCY_STATUS_DOES_NOT_EXIST:
                agency.create(agency_json_str)
                if agency.status == AGENCY_STATUS_EXISTS:
                    rc = True
                    error = err_ok
                else:
                    rc = False
                    error = construct_error_message(
                        agency.status,
                        agency.http_code,
                        agency.http_content,
                        agency_name,
                    )
            else:
                error = (
                    f"Agency {agency_name} already exists with status "
                    f"= {agency.status}, no changes made"
                )
        else:
            error = f"Missing NULL_GUID in {agency_name}.json file"
    else:
        error = f"Missing {agency_name}.json file"
    return rc, error


def new_phaseselector(region_name, agency_name, phaseselector_name):
    rc = False
    error = None
    phaseselector_json_str = get_json(phaseselector_name)
    if not phaseselector_json_str:
        error = f"Missing {phaseselector_name}.json file"
        return rc, error

    phaseselector = Phaseselector(region_name, agency_name, phaseselector_name)
    if phaseselector.status != DEVICE_STATUS_DOES_NOT_EXIST:
        error = (
            f"Agency {agency_name} does not exist or phaseselector {phaseselector_name}"
            f" already exists. No changes made"
        )
        return rc, error

    phaseselector.create(phaseselector_json_str)
    if phaseselector.status == DEVICE_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            phaseselector.status,
            phaseselector.http_code,
            phaseselector.http_content,
            phaseselector_name,
        )
        return rc, error


def new_vehicle(region_name, agency_name, vehicle_name):
    rc = False
    error = None
    vehicle_json_str = get_json(vehicle_name)
    if not vehicle_json_str:
        error = f"Missing {vehicle_name}.json file"
        return rc, error

    if "NULL_GUID" not in vehicle_json_str:
        error = f"Missing NULL_GUID in {vehicle_name}.json file"

    guid_str = str(uuid.uuid1()).upper()
    vehicle_json_str = vehicle_json_str.replace("NULL_GUID", guid_str)
    vehicle = Vehicle(region_name, agency_name, vehicle_name)
    if vehicle.status != DEVICE_STATUS_DOES_NOT_EXIST:
        error = (
            f"Agency {agency_name} does not exist or vehicle"
            f" {vehicle_name} already exists. No changes made"
        )
        return rc, error

    vehicle.create(vehicle_json_str)
    if vehicle.status == DEVICE_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            vehicle.status, vehicle.http_code, vehicle.http_content, vehicle_name
        )
        return rc, error


def new_communicator(region_name, agency_name, vehicle_name, communicator_name):
    rc = False
    error = None
    communicator_json_str = get_json(communicator_name)
    if not communicator_json_str:
        error = f"Missing {communicator_name}.json file"
        return rc, error

    if "NULL_GUID" not in communicator_json_str:
        error = f"Missing NULL_GUID in {communicator_name}.json file"

    guid_str = str(uuid.uuid1()).upper()
    communicator_json_str = communicator_json_str.replace("NULL_GUID", guid_str)
    communicator = Communicator(
        region_name, agency_name, vehicle_name, communicator_name
    )
    if communicator.status != DEVICE_STATUS_DOES_NOT_EXIST:
        error = (
            f"Agency {agency_name} does not exist or communicator "
            f"{communicator_name} already exists. No changes made"
        )
        return rc, error

    communicator.create(communicator_json_str)
    if communicator.status == DEVICE_STATUS_EXISTS:
        rc = True
        error = err_ok
    elif communicator.status == DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB:
        error = construct_error_message(
            communicator.status,
            communicator.http_code,
            communicator.asso_content,
            communicator_name,
        )
    else:
        error = construct_error_message(
            communicator.status,
            communicator.http_code,
            communicator.http_content,
            communicator_name,
        )
    return rc, error


def new_location(region_name, agency_name, location_name):
    rc = False
    error = None
    location_json_str = get_json(location_name)
    if location_json_str:
        location = Location(region_name, agency_name, location_name)
        if location.status == LOCATION_STATUS_DOES_NOT_EXIST:
            location.create(location_json_str)
            if location.status == LOCATION_STATUS_EXISTS:
                rc = True
                error = err_ok
            else:
                rc = False
                error = construct_error_message(
                    location.status,
                    location.http_code,
                    location.http_content,
                    location_name,
                )
        else:
            error = (
                f"Location {location_name} already exists with status "
                f"= {location.status}, no changes made"
            )
    else:
        error = f"Missing {location_name}.json file"
    return rc, error


def del_region(region_name):
    rc = False
    error = None
    region = Region(region_name)
    if region.status != REGION_STATUS_DOES_NOT_EXIST:
        region.delete()
        if region.status == REGION_STATUS_DOES_NOT_EXIST:
            rc = True
        error = f"Region {region_name} Delete Status = {region.status}"
    else:
        error = (
            f"Region {region_name} does not exists with status = "
            f"{region.status}, no changes made"
        )
    return rc, error


def del_agency(region_name, agency_name):
    rc = False
    error = None
    agency = Agency(region_name, agency_name)
    if agency.status != AGENCY_STATUS_DOES_NOT_EXIST:
        agency.delete()
        if agency.status == AGENCY_STATUS_DOES_NOT_EXIST:
            rc = True
        error = f"Agency {agency_name} Delete Status = {agency.status}"
    else:
        error = (
            f"Agency {agency_name} does not exists with status = "
            f"{agency.status}, no changes made"
        )
    return rc, error


def del_phaseselector(region_name, agency_name, phaseselector_name):
    rc = False
    error = None
    phaseselector = Phaseselector(region_name, agency_name, phaseselector_name)
    if phaseselector.status != DEVICE_STATUS_DOES_NOT_EXIST:
        phaseselector.delete()
        if phaseselector.status == DEVICE_STATUS_DOES_NOT_EXIST:
            rc = True
        error = f"Phase selector {phaseselector_name} Status = {phaseselector.status}"
    else:
        error = (
            f"Phase selector {phaseselector_name} in Agency "
            f"{agency_name} does not exist or does not have cert. "
            f"Status = {phaseselector.status}. No changes made"
        )
    return rc, error


def del_vehicle(region_name, agency_name, vehicle_name):
    rc = False
    error = None
    vehicle = Vehicle(region_name, agency_name, vehicle_name)
    if vehicle.status != DEVICE_STATUS_DOES_NOT_EXIST:
        vehicle.delete()
        if vehicle.status == DEVICE_STATUS_DOES_NOT_EXIST:
            rc = True
        error = f"Vehicle {vehicle_name} Status = {vehicle.status}"
    else:
        error = (
            f"Vehicle {vehicle_name} in Agency {agency_name} does not "
            f"exist or does not have cert. Status = {vehicle.status}. No changes made"
        )
    return rc, error


def del_communicator(region_name, agency_name, vehicle_name, communicator_name):
    rc = False
    error = None
    communicator = Communicator(
        region_name, agency_name, vehicle_name, communicator_name
    )
    if communicator.status != DEVICE_STATUS_DOES_NOT_EXIST:
        communicator.delete()
        if communicator.status == DEVICE_STATUS_DOES_NOT_EXIST:
            rc = True
        error = f"Communicator Status = {communicator.status}"
    else:
        error = (
            f"Communicator {communicator_name} in Agency {agency_name} "
            f"does not exist or does not have cert. Status = "
            f"{communicator.status}. No changes made"
        )
    return rc, error


def del_location(region_name, agency_name, location_name):
    rc = False
    error = None
    location = Location(region_name, agency_name, location_name)
    if location.status != LOCATION_STATUS_DOES_NOT_EXIST:
        location.delete()
        if location.status == LOCATION_STATUS_DOES_NOT_EXIST:
            rc = True
        error = f"Location {location_name} Delete Status = {location.status}"
    else:
        error = (
            f"Location {location_name} does not exists with status = "
            f"{location.status}, no changes made"
        )
    return rc, error


def update_region(region_name):
    rc = False
    error = None
    region_json_str = get_json(region_name)
    if not region_json_str:
        error = f"Missing {region_name}.json file"
        return rc, error

    region = Region(region_name)
    region.write(region_json_str)
    if region.status == REGION_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            region.status,
            region.http_response,
            region.http_content,
            region_name,
        )
        return rc, error


def update_agency(region_name, agency_name):
    rc = False
    error = None
    agency_json_str = get_json(agency_name)
    check_guid_regex = (
        "^[{]?[0-9a-fA-F]{8}" + "-([0-9a-fA-F]{4}-)" + "{3}[0-9a-fA-F]{12}[}]?$"
    )  # noqa: E501
    compiled_regex = re.compile(check_guid_regex)

    if not agency_json_str:
        error = f"Missing {agency_name}.json file"
        return rc, error
    agency_json = json.loads(agency_json_str)
    if "CMSId" not in agency_json_str:
        agency_json["attributes"]["CMSId"] = agency_json["attributes"][
            "agencyID"
        ].upper()
    if not re.search(compiled_regex, agency_json["attributes"]["CMSId"]):
        error = "CMSId provided is not a valid GUID"
        return rc, error
    agency_json_str = json.dumps(agency_json)

    # update the agency
    agency = Agency(region_name, agency_name)
    agency.write(agency_json_str)
    if agency.status == AGENCY_STATUS_EXISTS:
        rc = True
        return rc, err_ok
    else:
        rc = False
        error = construct_error_message(
            agency.status,
            agency.http_response,
            agency.http_content,
            agency_name,
        )
        return rc, error


def update_phaseselector(region_name, agency_name, phaseselector_name):
    rc = False
    error = None
    phaseselector_json_str = get_json(phaseselector_name)
    if not phaseselector_json_str:
        error = f"Missing {phaseselector_name}.json file"
        return rc, error

    phaseselector = Phaseselector(region_name, agency_name, phaseselector_name)
    phaseselector.write(phaseselector_json_str)
    if phaseselector.status == DEVICE_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            phaseselector.status,
            phaseselector.http_response,
            phaseselector.http_content,
            phaseselector_name,
        )
        return rc, error


def update_vehicle(region_name, agency_name, vehicle_name):
    rc = False
    error = None
    vehicle_json_str = get_json(vehicle_name)
    if not vehicle_json_str:
        error = f"Missing {vehicle_name}.json file"
        return rc, error

    vehicle = Vehicle(region_name, agency_name, vehicle_name)
    vehicle.write(vehicle_json_str)
    if vehicle.status == DEVICE_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            vehicle.status,
            vehicle.http_response,
            vehicle.http_content,
            vehicle,
        )
        return rc, error


def update_communicator(region_name, agency_name, vehicle_name, communicator_name):
    rc = False
    error = None
    communicator_json_str = get_json(communicator_name)
    if not communicator_json_str:
        error = f"Missing {communicator_name}.json file"
        return rc, error

    communicator = Communicator(
        region_name, agency_name, vehicle_name, communicator_name
    )
    communicator.write(communicator_json_str)
    if communicator.status == DEVICE_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            communicator.status,
            communicator.http_response,
            communicator.http_content,
            communicator_name,
        )
        return rc, error


def update_location(region_name, agency_name, location_name):
    rc = False
    error = None
    location_json_str = get_json(location_name)
    if not location_json_str:
        error = f"Missing {location_name}.json file"
        return rc, error

    location = Location(region_name, agency_name, location_name)
    location.write(location_json_str)
    if location.status == LOCATION_STATUS_EXISTS:
        return True, err_ok
    else:
        error = construct_error_message(
            location.status,
            location.http_response,
            location.http_content,
            location,
        )
        return rc, error


def list_regions(print_regions=False):
    rc = False
    region_list_array = []
    alib_rc, list_all_regions_content = alib.list_all_regions()
    if logs:
        print(f"HTTP Response = {alib_rc}")
    if alib_rc >= 200 and alib_rc < 300:
        list_all_regions_json_obj = json.loads(list_all_regions_content)
        if type(list_all_regions_json_obj) == dict:
            region_list_array = list_all_regions_json_obj.get("results", None)
            if type(region_list_array) == list:
                rc = True
                if print_regions:
                    for region in region_list_array:
                        print(f"region = {region}")
            elif logs:
                region_list_array = []
                print("Content of HTTP response is a list of regions")
        elif logs:
            print("Content of HTTP response is not a dictionary")
    else:
        print(f"HTTP response = {alib_rc}")

    return rc, region_list_array


def list_agencies(region_name, print_agencies=False):
    rc = False
    agency_list_array = []
    alib_rc, list_all_agencies_content = alib.list_all_agencies_in_region(region_name)
    if logs:
        print(f"HTTP Response = {alib_rc}")
    if alib_rc >= 200 and alib_rc < 300:
        list_all_agencies_json_obj = json.loads(list_all_agencies_content)
        if type(list_all_agencies_json_obj) == dict:
            agency_list_array = list_all_agencies_json_obj.get("results", None)
            if type(agency_list_array) == list:
                rc = True
                if print_agencies:
                    for agency in agency_list_array:
                        print(f"agency = {agency}")
            elif logs:
                agency_list_array = []
                print("Content of HTTP response is a list of agencies")
        elif logs:
            print("Content of HTTP response is not a dictionary")
    else:
        print(f"HTTP response = {alib_rc}")
    return rc, agency_list_array


# list phase selectors, vehicles and communicators owned by an agency
def list_devices(region_name, agency_name, print_devices=False):
    rc = False
    device_list_array = []
    alib_rc, list_all_devices_content = alib.list_all_devices_in_agency(
        region_name, agency_name
    )
    if logs:
        print(f"HTTP Response = {alib_rc}")
        print(f"response content = {list_all_devices_content}")
    if alib_rc >= 200 and alib_rc < 300:
        list_all_devices_json_obj = json.loads(list_all_devices_content)
        if type(list_all_devices_json_obj) == dict:
            device_list_array = list_all_devices_json_obj.get("results", None)
            if type(device_list_array) == list:
                rc = True
                for device in device_list_array:
                    if print_devices:
                        print(f"device = {device}")
            elif logs:
                print("Content of HTTP response is a list of agencies")
        elif logs:
            print("Content of HTTP response is not a dictionary")
    else:
        print(f"HTTP response = {alib_rc}")

    return rc, device_list_array


# list vehicles owned by an agency
def list_vehicles(region_name, agency_name):
    rc = False
    vehicle_list_array = []
    alib_rc, list_all_vehicles_content = alib.list_all_vehicles_in_agency(
        region_name, agency_name
    )
    if logs:
        print(f"HTTP Response = {alib_rc}")
        print(f"response content = {list_all_vehicles_content}")
    if alib_rc >= 200 and alib_rc < 300:
        list_all_vehicles_json_obj = json.loads(list_all_vehicles_content)
        if type(list_all_vehicles_json_obj) == dict:
            vehicle_list_array = list_all_vehicles_json_obj.get("results", None)
            if type(vehicle_list_array) == list:
                rc = True
            elif logs:
                print("Content of HTTP response is a list of vehicles")
        elif logs:
            print("Content of HTTP response is not a dictionary")
    else:
        print(f"HTTP response = {alib_rc}")

    return rc, vehicle_list_array


# list communicators installed at a vehicle
def list_communicators(vehicle_name, print_communicators=False):
    rc = False
    communicator_list_array = []
    alib_rc, list_all_communicators_content = alib.list_all_communicators_in_vehicle(
        vehicle_name
    )
    if logs:
        print(f"HTTP Response = {alib_rc}")
        print(f"response content = {list_all_communicators_content}")
    if alib_rc >= 200 and alib_rc < 300:
        list_all_communicators_json_obj = json.loads(list_all_communicators_content)
        if type(list_all_communicators_json_obj) == dict:
            communicator_list_array = list_all_communicators_json_obj.get(
                "results", None
            )
            if type(communicator_list_array) == list:
                rc = True
                for communicator in communicator_list_array:
                    if print_communicators:
                        print(f"communicator = {communicator}")
            elif logs:
                print("communicator_list_array is not a list")
        elif logs:
            print("Content of HTTP response is not a dictionary")
    else:
        print(f"HTTP response = {alib_rc}")

    return rc, communicator_list_array


def list_locations(print_locations=False):
    rc = False
    location_list_array = []
    alib_rc, list_all_locations_content = alib.list_all_locations()
    if logs:
        print(f"HTTP Response = {alib_rc}")
    if alib_rc >= 200 and alib_rc < 300:
        list_all_locations_json_obj = json.loads(list_all_locations_content)
        if type(list_all_locations_json_obj) == dict:
            location_list_array = list_all_locations_json_obj.get("results", None)
            if type(location_list_array) == list:
                rc = True
                if print_locations:
                    for location in location_list_array:
                        print(f"location = {location}")
            elif logs:
                location_list_array = []
                print("Content of HTTP response is a list of locations")
        elif logs:
            print("Content of HTTP response is not a dictionary")
    else:
        print(f"HTTP response = {alib_rc}")

    return rc, location_list_array


def main():
    error = None
    argp = argparse.ArgumentParser(description="GTT create CA in AWS")
    argp.add_argument("--logs", action="store_true", help="turn on logs")
    argp.add_argument("--new_reg", metavar="", help="--new_reg <region>")
    argp.add_argument("--del_reg", metavar="", help="--del_reg <region>")
    argp.add_argument(
        "--new_agy", metavar="", help="--new_agy <agency> --region <region>"
    )
    argp.add_argument(
        "--del_agy", metavar="", help="--del_agy <agency> --region <region>"
    )
    argp.add_argument(
        "--new_veh",
        metavar="",
        help="--new_veh <vehicle> --agency <agency> --region <region>",
    )
    argp.add_argument(
        "--del_veh",
        metavar="",
        help="--del_veh <vehicle> --agency <agency> --region <region>",
    )
    argp.add_argument(
        "--new_ps",
        metavar="",
        help="--new_ps <phaseselector> --agency <agency> --region <region>",
    )
    argp.add_argument(
        "--del_ps",
        metavar="",
        help="--del_ps <phaseselector> --agency <agency> --region <region>",
    )
    argp.add_argument(
        "--new_com",
        metavar="",
        help=(
            "--new_com <communicator> --vehicle <vehicle> "
            "--agency <agency> --region <region>"
        ),
    )
    argp.add_argument(
        "--del_com",
        metavar="",
        help=(
            "--del_com <communicator> --vehicle <vehicle> "
            "--agency <agency> --region <region>"
        ),
    )
    argp.add_argument(
        "--region", metavar="", help="--new_agy|--del_agy <agency> --region <region>"
    )
    argp.add_argument(
        "--agency", metavar="", help="--new_veh|--del_veh <device> --agency <agency>"
    )
    argp.add_argument(
        "--vehicle",
        metavar="",
        help="--new_veh|--del_veh <vehicle> --agency <agency> --region <region>",
    )
    argp.add_argument("--region_list", action="store_true", help="--region_list")
    argp.add_argument("--agency_list", metavar="", help="--agency_list <region>")
    argp.add_argument(
        "--device_list", metavar="", help="--device_list <agency> --region <region>"
    )
    argp.add_argument(
        "--communicator_list", metavar="", help="--communicator_list <vehicle>"
    )
    args = argp.parse_args()

    logs = args.logs
    # logs = True
    if logs:
        print(
            f"logs = {args.logs}, new_agy = {args.new_agy}, del_agy = {args.del_agy}, "
            f"new_ps = {args.new_ps}, del_ps = {args.del_ps},new_veh = {args.new_veh}, "
            f"del_veh = {args.del_veh}, agency = {args.agency},agency_list = "
            f"{args.agency_list}, device_list = {args.device_list}, "
            f"communicator_list = {args.communicator_list}"
        )

    if args.new_reg:
        _, error = new_region(args.new_reg)

    elif args.new_agy and args.region:
        _, error = new_agency(args.region, args.new_agy)

    elif args.new_veh and args.agency and args.region:
        _, error = new_vehicle(args.region, args.agency, args.new_veh)

    elif args.new_ps and args.agency and args.region:
        _, error = new_phaseselector(args.region, args.agency, args.new_ps)

    elif args.new_com and args.vehicle and args.agency and args.region:
        if args.vehicle == "None":
            args.vehicle = None
        _, error = new_communicator(
            args.region, args.agency, args.vehicle, args.new_com
        )

    elif args.del_reg:
        _, error = del_region(args.del_reg)

    elif args.del_agy and args.region:
        _, error = del_agency(args.region, args.del_agy)

    elif args.del_veh and args.agency and args.region:
        _, error = del_vehicle(args.region, args.agency, args.del_veh)

    elif args.del_ps and args.agency and args.region:
        _, error = del_phaseselector(args.region, args.agency, args.del_ps)

    elif args.del_com and args.vehicle and args.agency and args.region:
        if args.vehicle == "None":
            args.vehicle = None
        _, error = del_communicator(
            args.region, args.agency, args.vehicle, args.del_com
        )

    elif args.region_list:
        list_regions(print_regions=True)

    elif args.agency_list:
        list_agencies(args.agency_list, print_agencies=True)

    elif args.device_list and args.region:
        list_devices(args.region, args.device_list, print_devices=True)

    elif args.communicator_list:
        list_communicators(args.communicator_list, print_communicators=True)

    else:
        argp.print_help()

    if error:
        print(error)


if __name__ == "__main__":
    main()
