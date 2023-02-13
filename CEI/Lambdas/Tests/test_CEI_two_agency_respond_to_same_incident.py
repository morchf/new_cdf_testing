# flake8: noqa
# fmt: off
"""
Test case:
Assign 2 agencies to an Incident and then check the activation status 
Deactivate incident for an an agency check the status for another agency
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

def test_two_agency_same_incident_report(setup):
    """Activate the first vehicle with first Agency"""
    run_API_incident_call("activate_vehicle_create_incident.json", False, False)

    time.sleep(2)
    run_API_incident_call("activate_vehicle_update_incident.json", True, True)

    """Activate the second vehicle with second Agency"""
    run_API_incident_call("second_agency_same_incident_report.json", False, False)

    time.sleep(2)
    run_API_incident_call("second_agency_same_incident_update.json", True, True)

    """Deactivate the v2 vehicle by setting the priority to none."""
    run_API_incident_call("deactivate_vehicle_using_incident.json", True, False)


    """Checking the vehicle from the second agency is still active"""
    run_priority_confirmation(True, region_name, agency_two_name, vehicle_two_device_id)
