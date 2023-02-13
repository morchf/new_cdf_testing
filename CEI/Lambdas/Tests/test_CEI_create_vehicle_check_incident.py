# flake8: noqa
# fmt: off
import time
import pytest
from CEI_TestSetup import *


@pytest.fixture(scope="module")
def setup():
    clear_test_data()
    create_region("CEIRegion.json").get("name")
    time.sleep(1)
    create_agency("CEIAgency.json").get("name")
    time.sleep(1)
    agency_name = create_agency("StandardAgency.json").get("name")
    time.sleep(1)

    vehicle_device_id = create_vehicle("CEIVehicleOne.json").get("deviceId")
    com_device_id = create_com("StandardComOne.json").get("deviceId")
    create_association(vehicle_device_id, com_device_id)

    time.sleep(1)


def test_activate_vehicle(setup):
    """Activate the vehicle"""
    run_API_incident_call("activate_vehicle_create_incident.json", False, False)

    time.sleep(2)
    run_API_incident_call("activate_vehicle_update_incident.json", True, True)


def test_deactivate_vehicle(setup):
    """Deactivate the v2 vehicle by setting the priority to none."""
    run_API_incident_call("deactivate_vehicle_update_incident.json", True, False)

# fmt: on
