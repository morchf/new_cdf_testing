# flake8: noqa
# fmt: off
import time
import pytest
from CEI_TestSetup import *


@pytest.fixture(scope="module")
def setup():
    clear_test_data()

    global region_name
    region_name = create_region("CEIRegion.json").get("name")
    time.sleep(1)
    create_agency("CEIAgency.json").get("name")
    time.sleep(1)
    
    create_agency("StandardAgency.json").get("name")
    time.sleep(1)

    vehicle_device_id = create_vehicle("CEIVehicleOne.json").get("deviceId")
    com_device_id = create_com("StandardComOne.json").get("deviceId")
    create_association(vehicle_device_id, com_device_id)

    global agency_two_name
    agency_two_name = create_agency("CEIAgencyTwo.json").get("name")
    time.sleep(1)

    global vehicle_two_device_id
    vehicle_two_device_id = create_vehicle("CEIVehicleTwo.json").get("deviceId")
    com_two_device_id = create_com("StandardComTwo.json").get("deviceId")

    create_association(vehicle_two_device_id, com_two_device_id)
    time.sleep(1)


def test_activate_vehicle(setup):
    """Activate the vehicle"""
    run_API_incident_call("activate_vehicle_create_incident.json", False, False)

    time.sleep(2)
    run_API_incident_call("activate_vehicle_update_incident.json", True, True)


def test_agency_isolation(setup):
    run_priority_confirmation(
        False, region_name, agency_two_name, vehicle_two_device_id
    )


def test_deactivate_vehicle(setup):
    """Deactivate the vehicle by setting the priority to none, reactivate,
    then deactivate the vehicle by setting the Unit Status to off.
    """

    print("Deactivating Vehicle 1 Via Unit...")
    run_API_incident_call("deactivate_vehicle_using_unit.json", True, False)

    print("Reactivating Vehicle 1 Via Unit...")
    run_API_incident_call("activate_vehicle_create_incident.json", False, False)

    print("Reactivating Vehicle 1 Via Unit...")
    run_API_incident_call("activate_vehicle_update_incident.json", True, True)

    print("Deactivating Vehicle 1 Via Incident...")
    run_API_incident_call("deactivate_vehicle_using_incident.json", True, False)

# fmt: on
