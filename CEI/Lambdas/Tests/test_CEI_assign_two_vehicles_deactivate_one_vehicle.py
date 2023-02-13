# flake8: noqa
# fmt: off
"""
Test case:
Assign 2 vehicles to an Incident and then deactivate One vehicle 
Create another incident and assign the deactivate vehicle to that incident
"""
import time
import pytest
from CEI_TestSetup import *


@pytest.fixture(scope="module")
def setup():
    clear_test_data()
    global region_name
    region_name = create_region("CEIRegion.json").get("name")
    time.sleep(1)

    global agency_name
    agency_name = create_agency("CEIAgency.json").get("name")
    time.sleep(1)

    standard_agency_name = create_agency("StandardAgency.json").get("name")
    time.sleep(1)

    vehicle_device_id = create_vehicle("CEIVehicleOne.json").get("deviceId")

    com_device_id = create_com("StandardComOne.json").get("deviceId")
    create_association(vehicle_device_id, com_device_id)

    global vehicle_two_device_id
    vehicle_two_device_id = create_vehicle("CEIVehicleThree.json").get("deviceId")
    com_two_device_id = create_com("StandardComThree.json").get("deviceId")
    create_association(vehicle_two_device_id, com_two_device_id)

    time.sleep(1)

def test_vehicles_active_status(setup):
    """Activate the vehicle"""
    run_API_incident_call("activate_vehicle_create_incident.json", False, False)

    time.sleep(2)
    run_API_incident_call("activate_two_vehicles_update_incident.json", True, True)

    """Deactivate the first vehicle and check the status of the second vehicle"""
    run_API_incident_call("deactivate_vehicle_using_unit.json", True, False)

    """Second vehicle status is still active"""
    run_priority_confirmation(True, region_name, agency_name, vehicle_two_device_id)


    """Create second incident for the agency and assing first vehicle"""
    run_API_incident_call("activate_vehicle_create_second_incident.json", False, False)

    time.sleep(2)
    run_API_incident_call("activate_vehicle_update_second_incident.json", True, True)

    """Deactivate the second incident and check the vehicle status"""
    run_API_incident_call("deactivate_vehicle_update_second_incident.json", True, False)
