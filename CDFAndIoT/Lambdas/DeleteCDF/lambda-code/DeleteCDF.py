import os
import sys
import collections

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)
from ui import (  # noqa: E402
    del_vehicle,
    del_communicator,
    del_phaseselector,
    del_agency,
    del_region,
    del_location,
    list_agencies,
    list_devices,
    list_vehicles,
)


def lambda_handler(event, context):
    rc = False

    taskResult = event.get("taskResult-consume-csv")

    if taskResult:
        regions = taskResult.get("regions")
        agencies = taskResult.get("agencies")
        vehicles = taskResult.get("vehicles")
        communicators = taskResult.get("communicators")
        phase_selectors = taskResult.get("phase_selectors")
        locations = taskResult.get("locations")
    else:
        raise Exception("No entities to delete")

    # delete devices first so that their agencies may be deleted(have no children)
    if communicators:
        to_delete = communicators.split(",")
        for items in to_delete:
            region = items.split("/")[0]
            agency = items.split("/")[1]
            communicator = items.split("/")[2]
            rc = del_communicator(region, agency, None, communicator)

    if vehicles:
        to_delete = vehicles.split(",")

        reg_agy_dict = collections.defaultdict(list)
        for item in to_delete:
            # item = "MINNESOTA/LAKEVILLE/SimDeviceTest0105Com"
            region_agency, veh_name = item.rsplit("/", 1)
            reg_agy_dict[region_agency].append(veh_name)

        for reg_agy, veh_name_list in reg_agy_dict.items():
            region, agency = reg_agy.split("/")

            # get vehicles' deviceId given their names
            _, vehicle_list = list_vehicles(region, agency)
            vehicle_dict = {
                x["attributes"]["name"]: x["deviceId"] for x in vehicle_list
            }
            for veh_name in veh_name_list:
                if veh_name in vehicle_dict:
                    veh_deviceId = vehicle_dict[veh_name]
                    rc = del_vehicle(region, agency, veh_deviceId)
                else:
                    rc = False
                    print(f"Agency {agency} has no vehicle {veh_name} to delete")

    if phase_selectors:
        to_delete = phase_selectors.split(",")
        for items in to_delete:
            region = items.split("/")[0]
            agency = items.split("/")[1]
            ps = items.split("/")[2]
            rc = del_phaseselector(region, agency, ps)

    if agencies:
        # check for orphans; delete if none
        to_delete = agencies.split(",")
        for items in to_delete:
            region = items.split("/")[0]
            agency = items.split("/")[1]
            rc, device_list = list_devices(region, agency)
            print(rc)
            print(device_list)
            # rc is False if agency has no children and device_list is empty
            if not device_list:
                rc = del_agency(region, agency)
            else:
                rc = False
                print(
                    f"Agency {agency} has children, cannot delete until children are removed"
                )

    if regions:
        # check for orphans; delete if none
        to_delete = regions.split(",")
        for items in to_delete:
            region = items.split("/")[0]
            rc, agency_list = list_agencies(region)
            print(rc)
            print(agency_list)
            # rc is False if agency has no children and agency_list is empty
            if not agency_list:
                rc = del_region(items)
            else:
                rc = False
                print(
                    f"Region {region} has children, cannot delete until children are removed"
                )

    if locations:
        # check for orphans; delete if none
        to_delete = locations.split(",")
        for items in to_delete:
            region = items.split("/")[0]
            agency = items.split("/")[1]
            location = items.split("/")[2]
            rc = del_location(region, agency, location)

    return rc
