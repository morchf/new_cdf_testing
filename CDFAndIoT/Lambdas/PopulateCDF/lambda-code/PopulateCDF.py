import json
import os
import sys

sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)
from ui import (  # noqa: E402
    new_region,
    new_agency,
    new_vehicle,
    new_communicator,
    new_phaseselector,
    new_location,
    list_regions,
    list_agencies,
    list_devices,
    del_region,
    del_agency,
    del_communicator,
    del_phaseselector,
)


def get_region_and_agency_name(input_data):
    groups = input_data.get("groups", "")
    ownedby = groups.get("ownedby", "")
    region = ownedby[0].split("/")[1]
    agency = ownedby[0].split("/")[2]
    return region, agency


def lambda_handler(event, context):
    rc = True

    # load json data
    # groups use name the unique identifier
    input_data = event["taskResult-create-json"]
    if input_data != None:  # noqa: E711
        input_data = input_data["entity_json"]
    else:
        raise Exception("input data not found")

    if input_data == "invalid":
        error = input_data.get("error")
        raise Exception(f"input data invalid, {error}")

    deviceId = input_data.get("deviceId")
    name = input_data.get("name", deviceId)

    templateId = input_data.get("templateId")
    if templateId == "communicator":
        vehicle = input_data.pop("vehicle")

    # save to /tmp directory
    fp = f"/tmp/{name}.json"
    with open(fp, "w") as file:
        json.dump(input_data, file)
    file.close()

    # decide which entity to create
    if templateId == "region":
        rc, error = new_region(name)

        # check regionGUID, caCertId uniqueness
        if rc:
            rc_unique, error_unique = check_unique_region(name)
            if not rc_unique:
                _ = del_region(name)
                rc, error = False, error_unique

    elif templateId == "agency":
        # Need to know region name to create agency
        region = input_data.get("parentPath", "")
        # Remove leading / from region name
        rc, error = new_agency(region.lstrip("/"), name)

        # check caCertId, vpsCertId uniqueness
        if rc:
            rc_unique, error_unique = check_unique_agency(name)
            if not rc_unique:
                _ = del_agency(region, name)
                rc, error = False, error_unique

    elif templateId == "vehicle" or templateId == "vehicleV2":
        region, agency = get_region_and_agency_name(input_data)
        rc, error = new_vehicle(region, agency, name)

    elif templateId == "communicator":
        region, agency = get_region_and_agency_name(input_data)
        if vehicle == "":
            vehicle = None
        rc, error = new_communicator(region, agency, vehicle, name)

        # check devCertId uniqueness
        if rc:
            rc_unique, error_unique = check_unique_device(name)
            if not rc_unique:
                _ = del_communicator(region, agency, vehicle, name)
                rc, error = False, error_unique

    elif templateId == "phaseselector":
        region, agency = get_region_and_agency_name(input_data)
        rc, error = new_phaseselector(region, agency, name)
        # check devCertId uniqueness
        if rc:
            rc_unique, error_unique = check_unique_device(name)
            if not rc_unique:
                _ = del_phaseselector(region, agency, name)
                rc, error = False, error_unique

    elif templateId == "location":
        _, region, agency = input_data.get("parentPath", "").split("/")
        rc, error = new_location(region, agency, name)

    else:
        rc, error = False, "Invalid input JSON"

    # remove json file
    os.remove(fp)

    return rc, error


def check_unique_region(name):
    rc, error = True, ""
    _, region_list = list_regions()
    cert_list, guid_list = [], []
    caCertId, regionGUID = None, None
    for region in region_list:
        tmp_region_name = region.get("name")
        if tmp_region_name == name:
            caCertId = region.get("attributes").get("caCertId")
            regionGUID = region.get("attributes").get("regionGUID")
        else:
            cert_list.append(region.get("attributes").get("caCertId"))
            guid_list.append(region.get("attributes").get("regionGUID"))

    if caCertId in cert_list or regionGUID in guid_list:
        rc, error = False, "region is not unique"
    return rc, error


def check_unique_agency(name):
    rc, error = True, ""
    ca_list, vps_list, id_list = [], [], []
    caCertId, vpsCertId, agencyID = None, None, None

    _, region_list = list_regions()
    for region in region_list:
        tmp_region_name = region.get("name")

        _, agency_list = list_agencies(tmp_region_name)
        for agency in agency_list:
            tmp_agency_name = agency.get("name")
            if tmp_agency_name == name:
                caCertId = agency.get("attributes").get("caCertId")
                vpsCertId = agency.get("attributes").get("vpsCertId")
                agencyID = agency.get("attributes").get("agencyID")
            else:
                ca_list.append(agency.get("attributes").get("caCertId"))
                vps_list.append(agency.get("attributes").get("vpsCertId"))
                id_list.append(agency.get("attributes").get("agencyID"))

    if caCertId in ca_list or vpsCertId in vps_list or agencyID in id_list:
        rc, error = False, "agency is not unique"
    return rc, error


def check_unique_device(name):
    rc, error = True, ""
    cert_list = []
    devCertId = None

    _, region_list = list_regions()
    for region in region_list:
        tmp_region_name = region.get("name")
        _, agency_list = list_agencies(tmp_region_name)
        for agency in agency_list:
            tmp_agency_name = agency.get("name")
            _, device_list = list_devices(tmp_region_name, tmp_agency_name)
            for device in device_list:
                tmp_device_id = device.get("deviceId")
                if tmp_device_id == name:
                    devCertId = device.get("attributes").get("devCertId", "")
                else:
                    cert_list.append(device.get("attributes").get("devCertId", ""))

    if devCertId in cert_list:
        rc = False
        error = "devCertId is " + devCertId + " while cert_list is " + str(cert_list)
    return rc, error
