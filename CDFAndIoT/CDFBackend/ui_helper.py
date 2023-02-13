import re
from ui import (
    list_regions,
    list_agencies,
    list_vehicles,
    list_devices,
)


def check_field_length(length_dict, data_dict, templateId):
    for item in length_dict:
        if item in ["deviceId", "description"]:
            data_length = len(data_dict.get(item))
        elif item == "name":
            if templateId == "vehiclev2":
                data_length = len(data_dict.get("attributes").get(item))
            else:
                data_length = len(data_dict.get(item))
        else:
            data_length = len(data_dict.get("attributes").get(item))
        allowed_length = length_dict[item]
        if data_length > allowed_length:
            raise Exception(
                f"The field {item} is {data_length} characters it must be "
                f"less than {allowed_length} charactor(s)"
            )


def validate_IMEI(imei):
    if not re.match("[0-9]{15}$", imei):
        raise Exception("IMEI is not valid")


def validate_MAC(mac_address):
    if not re.match(
        "[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address.lower()
    ):
        raise Exception("MAC address is not valid")


def check_unique_agency(entity_dict):
    curr_agencyCode = entity_dict["attributes"]["agencyCode"]
    curr_name = entity_dict["name"]
    _, cur_reg, _ = entity_dict["groupPath"].split("/")
    _, agency_list = list_agencies(cur_reg)
    for agency in agency_list:
        tmp_agency_name = agency.get("name")
        if tmp_agency_name == curr_name:
            continue
        if agency.get("attributes") and agency.get("attributes").get("agencyCode"):
            if agency.get("attributes").get("agencyCode") == curr_agencyCode:
                raise Exception("Error: agencyCode already exists in agency")


def check_unique_vehicle(data):
    """
    vehicle name needs to be unique and nonnull within an agency
    """
    curr_veh_Id = data["deviceId"]
    if data.get("attributes") and data.get("attributes").get("name") != "":
        curr_name = data["attributes"]["name"]
    else:
        raise Exception("Error: vehicle name must be non-empty")
    _, reg_name, agy_name = data["groups"]["ownedby"][0].rsplit("/")
    _, vehicle_list_array = list_vehicles(reg_name, agy_name)

    for vehicle in vehicle_list_array:
        tmp_veh_id = vehicle.get("deviceId")
        if tmp_veh_id == curr_veh_Id:
            continue
        if vehicle.get("attributes") and vehicle.get("attributes").get("name"):
            if vehicle.get("attributes").get("name") == curr_name:
                raise Exception(
                    f"Error: vehicle name already exists in agency {agy_name}"
                )


def check_unique_device(data, uniqueList):
    current_deviceId = data["deviceId"]
    _, region_list = list_regions()
    for region in region_list:
        tmp_region_name = region.get("name")
        if tmp_region_name == "region":
            pass
        _, agency_list = list_agencies(tmp_region_name)
        for agency in agency_list:
            tmp_agency_name = agency.get("name")
            if tmp_agency_name == "agency":
                pass
            _, device_list = list_devices(tmp_region_name, tmp_agency_name)
            for device in device_list:
                tmp_deviceId = device.get("deviceId")
                if tmp_deviceId == current_deviceId:
                    continue
                for field_name in uniqueList:
                    if device.get("attributes") and device.get("attributes").get(
                        field_name
                    ):
                        if (
                            device.get("attributes").get(field_name)
                            == data["attributes"][field_name]
                        ):
                            raise Exception(
                                f"Error: {field_name} already exists in device"
                            )


def get_region_and_agency_name(input_data):
    groups = input_data.get("groups", "")
    if "out" in groups:
        out = groups.get("out", "")
        ownedby = out.get("ownedby", "")
    else:
        ownedby = groups.get("ownedby", "")
    region = ownedby[0].split("/")[1]
    agency = ownedby[0].split("/")[2]
    return region, agency
