"""
    test_asset_lib.py provides a test frame work for asset_lib.py.
    Test cases are create, delete, list, write to entities using region template.
    Test cases are create, delete, list, write to entities using agency template.
    Test cases are create, delete, list, write to entities using vehicle template.
    The region for an agency must be created first. The agency for a vehicle must
    be created second. The vehicle json file identifies which agency it is being
    create under.
    All tests leave the asset library in the same state as before starting the test,
    e.g. if an agency is created then that agency is deleted.
"""
import pytest
import json
from ui import (
    new_region,
    del_region,
    new_agency,
    del_agency,
    new_phaseselector,
    del_phaseselector,
    new_vehicle,
    del_vehicle,
    new_communicator,
    del_communicator,
    list_regions,
    list_agencies,
    list_devices,
    list_communicators,
)
from asset_lib import agency_read, device_read

log = True


def local_create_communicator(
    region_name, agency_name, vehicle_name, communicator_name
):
    rc = new_communicator(region_name, agency_name, vehicle_name, communicator_name)
    assert rc, (
        f"Error new_communicator(). region_name = {region_name}. "
        f"agency_name = {agency_name}. vehicle_name = {vehicle_name}. "
        f"communicator_name = {communicator_name}"
    )


def local_delete_communicator(
    region_name, agency_name, vehicle_name, communicator_name
):
    rc = del_communicator(region_name, agency_name, vehicle_name, communicator_name)
    assert rc, (
        f"Error del_communicator(). region_name = {region_name}. "
        f"agency_name = {agency_name}. vehicle_name = {vehicle_name}. "
        f"communicator_name = {communicator_name}"
    )


def local_create_vehicle(region_name, agency_name, vehicle_name):
    rc = new_vehicle(region_name, agency_name, vehicle_name)
    assert rc, (
        f"Error new_vehicle(). region_name = {region_name}. "
        f"agency_name = {agency_name}. vehicle_name = {vehicle_name}"
    )


def local_delete_vehicle(region_name, agency_name, vehicle_name):
    rc = del_vehicle(region_name, agency_name, vehicle_name)
    assert rc, (
        f"Error del_vehicle(). region_name = {region_name}. "
        f"agency_name = {agency_name}. vehicle_name = {vehicle_name}"
    )


def local_create_phaseselector(region_name, agency_name, phaseselector_name):
    rc = new_phaseselector(region_name, agency_name, phaseselector_name)
    assert rc, (
        f"Error new_phaseselector(). region_name = {region_name}. "
        f"agency_name = {agency_name}. phaseselector_name = {phaseselector_name}"
    )


def local_delete_phaseselector(region_name, agency_name, phaseselector_name):
    rc = del_phaseselector(region_name, agency_name, phaseselector_name)
    assert rc, (
        f"Error del_phaseselector(). region_name = {region_name}. "
        f"agency_name = {agency_name}. phaseselector_name = {phaseselector_name}"
    )


def local_create_agency(region_name, agency_name):
    rc = new_agency(region_name, agency_name)
    assert (
        rc
    ), f"Error new_agency(). region_name = {region_name}. agency_name = {agency_name}."


def local_delete_agency(region_name, agency_name):
    rc = del_agency(region_name, agency_name)
    assert (
        rc
    ), f"Error del_agency(). region_name = {region_name}. agency_name = {agency_name}."


def local_create_region(region_name):
    rc = new_region(region_name)
    assert rc, f"Error new_region(). region_name = {region_name}"


def local_delete_region(region_name):
    rc = del_region(region_name)
    assert rc, f"Error del_region(). region_name = {region_name}"


class TestUi:
    @pytest.fixture(scope="function", autouse=True)
    def tearDown(self):
        del_communicator("r1", "a1", "v1", "c3")
        del_communicator("r1", "a1", "v1", "C2")
        del_communicator("r1", "a1", "v1", "c1")
        del_vehicle("r1", "a1", "V11")
        del_vehicle("r1", "a1", "v1")
        del_phaseselector("r1", "a1", "PS2")
        del_phaseselector("r1", "a1", "ps1")
        del_agency("r1", "A2")
        del_agency("r1", "a1")
        del_region("R2")
        del_region("r1")

    """
        Create and Delete a Region
    """

    def test_region(self):
        region_name = "r1"
        local_create_region(region_name)
        local_delete_region(region_name)

    """
        Create and Delete an Agency
    """

    def test_agency(self):
        region_name = "r1"
        agency_name = "a1"
        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create and Delete a Phase Selector
    """

    def test_phaseselector(self):
        region_name = "r1"
        agency_name = "a1"
        phaseselector_name = "ps1"
        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        local_create_phaseselector(region_name, agency_name, phaseselector_name)
        local_delete_phaseselector(region_name, agency_name, phaseselector_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create and Delete a Vehicle
    """

    def test_vehicle(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        local_create_vehicle(region_name, agency_name, vehicle_name)
        local_delete_vehicle(region_name, agency_name, vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create and Delete a Communicator
    """

    def test_communicator(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        communicator_name = "c1"
        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        local_create_vehicle(region_name, agency_name, vehicle_name)
        local_create_communicator(
            region_name, agency_name, vehicle_name, communicator_name
        )
        local_delete_communicator(
            region_name, agency_name, vehicle_name, communicator_name
        )
        local_delete_vehicle(region_name, agency_name, vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create region, and agency and list agencies then delete everybody
    """

    def test_list_communicators(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        communicator_list = ["c1", "C2"]
        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        local_create_vehicle(region_name, agency_name, vehicle_name)
        for communicator_name in communicator_list:
            local_create_communicator(
                region_name, agency_name, vehicle_name, communicator_name
            )

        alib_rc, alib_communicator_list = list_communicators(
            vehicle_name, print_communicators=True
        )
        assert alib_rc, (
            f"Error list_communicators(). region_name = {region_name}. "
            f"agency_name = {agency_name}. vehicle_name = {vehicle_name}"
        )
        rc = True
        not_found_communicator = None

        for communicator_name in communicator_list:
            # Asset lib auto converts all deviceIds to lower case
            communicator_name = communicator_name.lower()
            # communicator_name = communicator_name.lower()
            print(f"communicator name = {communicator_name}")
            for alib_communicator in alib_communicator_list:
                print(f"alib_communicator = {alib_communicator}")
                if alib_communicator.get("deviceId", None) == communicator_name:
                    break
            else:
                not_found_communicator = communicator_name
                rc = False
                break
        assert rc, (
            f"Error an added communicator not found. "
            f"communicator_name not found = {not_found_communicator}"
        )

        # Now delete vehicle, agency, and region
        for communicator_name in communicator_list:
            local_delete_communicator(
                region_name, agency_name, vehicle_name, communicator_name
            )
        local_create_vehicle(region_name, agency_name, vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create region, agency, and vehicles and list vehicles then delete everybody
    """

    def test_list_devices(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        vehicle_list = ["v1", "V11"]
        phaseselector_list = ["ps1", "PS2"]
        communicator_list = ["c1", "C2"]
        device_list = vehicle_list + phaseselector_list + communicator_list

        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        for vehicle_name in vehicle_list:
            local_create_vehicle(region_name, agency_name, vehicle_name)
        for phaseselector_name in phaseselector_list:
            local_create_phaseselector(region_name, agency_name, phaseselector_name)
        for communicator_name in communicator_list:
            local_create_communicator(
                region_name, agency_name, vehicle_name, communicator_name
            )

        alib_rc, alib_device_list = list_devices(region_name, agency_name)
        assert alib_rc, (
            f"Error list_devices(). region_name = {region_name}. "
            f"agency_name = {agency_name}."
        )
        rc = True
        not_found_device = None
        for device_name in device_list:
            # Asset lib auto converts all deviceIds to lower case
            device_name = device_name.lower()
            print(f"device name = {device_name}")
            for alib_device in alib_device_list:
                print(f"alib_device = {alib_device}")
                if alib_device.get("deviceId", None) == device_name:
                    break
            else:
                not_found_device = device_name
                rc = False
                break
        assert (
            rc
        ), f"Error an added device not found.device_name not found = {not_found_device}"

        # Now delete vehicle, agency, and region
        for communicator_name in communicator_list:
            local_delete_communicator(
                region_name, agency_name, vehicle_name, communicator_name
            )
        for vehicle_name in vehicle_list:
            local_delete_vehicle(region_name, agency_name, vehicle_name)
        for phaseselector_name in phaseselector_list:
            local_delete_phaseselector(region_name, agency_name, phaseselector_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create region, and agency and list agencies then delete everybody
    """

    def test_list_agencies(self):
        region_name = "r1"
        agency_list = ["a1", "A2"]
        local_create_region(region_name)
        for agency_name in agency_list:
            local_create_agency(region_name, agency_name)

        alib_rc, alib_agency_list = list_agencies(region_name)
        assert alib_rc, "Error list_agencies()"
        rc = True
        not_found_agency = None
        for agency_name in agency_list:
            print(f"agency_name = {agency_name}")

            for alib_agency in alib_agency_list:
                print(f"alib_agency = {alib_agency}")
                if alib_agency.get("name", None) == agency_name:
                    break
            else:
                not_found_agency = agency_name
                rc = False
                break
        assert (
            rc
        ), f"Error an added agency not found. agency_name not found={not_found_agency}"

        for agency_name in agency_list:
            local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create list regions then delete
    """

    def test_list_regions(self):
        region_list = ["r1", "R2"]
        for region_name in region_list:
            local_create_region(region_name)

        alib_rc, alib_region_list = list_regions()
        assert alib_rc, "Error list_agencies()"
        print("!!!!!!!!!!!alib_region_list" + str(alib_region_list))
        rc = True
        not_found_region = None
        for region_name in region_list:
            print(f"region_name = {region_name}")

            for alib_region in alib_region_list:
                print(f"alib_region = {alib_region}")
                if alib_region.get("name", None) == region_name:
                    break
            else:
                not_found_region = region_name
                rc = False
                break
        assert (
            rc
        ), f"Error an added region not found. region_name not found={not_found_region}"

        for region_name in region_list:
            local_delete_region(region_name)

    def test_region_failed_validation(self):
        region_name = "r1_fv"

        rc, content = new_region(region_name)
        assert content == (
            'An error has occurred, 400, b\'{"error":"FAILED_VALIDATION"}\'. '
            "Entity create status is REGION_STATUS_DOES_NOT_EXIST"
        )
        assert not rc, f"Region did not fail create as expected, {content}"

    def test_agency_failed_validation(self):
        region_name = "r1"
        agency_name = "a1_fv"

        local_create_region(region_name)

        rc, content = new_agency(region_name, agency_name)
        assert content == (
            'An error has occurred, 400, b\'{"error":"FAILED_VALIDATION"}\'. '
            "Entity create status is AGENCY_STATUS_DOES_NOT_EXIST"
        )
        assert not rc, f"Agency did not fail create as expected, {content}"

        local_delete_region(region_name)

    def test_vehicle_failed_validation(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1_fv"

        local_create_region(region_name)
        local_create_agency(region_name, agency_name)

        rc, content = new_vehicle(region_name, agency_name, vehicle_name)

        assert content == (
            'An error has occurred, 400, b\'{"error":"FAILED_VALIDATION"}\'. '
            "Entity create status is DEVICE_STATUS_DOES_NOT_EXIST"
        )
        assert not rc, f"Vehicle did not fail create as expected, {content}"

        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_vehicle_invalid_relation(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1_ir"

        local_create_region(region_name)
        local_create_agency(region_name, agency_name)

        rc, content = new_vehicle(region_name, agency_name, vehicle_name)

        assert content == (
            'An error has occurred, 400, b\'{"error":"INVALID_RELATION"}\'. '
            "Entity create status is DEVICE_STATUS_DOES_NOT_EXIST"
        )
        assert not rc, f"Vehicle did not fail create as expected, {content}"

        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_phase_selector_failed_validation(self):
        region_name = "r1"
        agency_name = "a1"
        ps_name = "ps1_fv"

        local_create_region(region_name)
        local_create_agency(region_name, agency_name)

        rc, content = new_phaseselector(region_name, agency_name, ps_name)
        assert content == (
            'An error has occurred, 400, b\'{"error":"FAILED_VALIDATION"}\'. '
            "Entity create status is DEVICE_STATUS_DOES_NOT_EXIST"
        )
        assert not rc, f"Phase selector did not fail create as expected, {content}"

        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_phase_selector_invalid_relation(self):
        region_name = "r1"
        agency_name = "a1"
        ps_name = "ps1_ir"

        local_create_region(region_name)
        local_create_agency(region_name, agency_name)

        rc, content = new_phaseselector(region_name, agency_name, ps_name)
        assert content == (
            'An error has occurred, 400, b\'{"error":"INVALID_RELATION"}\'. '
            "Entity create status is DEVICE_STATUS_DOES_NOT_EXIST"
        )
        assert not rc, f"Phase selector did not fail create as expected, {content}"

        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_2100_cert_generation(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"

        # step 1. create c3 whose model is mp-70, expect creation of
        # device cert and update communicator entity
        communicator_mp70_name = "c3"
        local_create_region(region_name)
        local_create_agency(region_name, agency_name)
        local_create_vehicle(region_name, agency_name, vehicle_name)
        local_create_communicator(
            region_name, agency_name, vehicle_name, communicator_mp70_name
        )
        agency_status, agency_content = agency_read(region_name, agency_name)
        assert 200 <= agency_status < 300, "Failed to read agency content"
        agency_json = json.loads(agency_content)
        Cert2100Id = agency_json["attributes"]["Cert2100Id"]
        assert Cert2100Id == "NULL_CERT", "MP-70 model generate 2100 cert"

        communicator_status, communicator_content = device_read(communicator_mp70_name)
        assert (
            200 <= communicator_status < 300
        ), f"Failed to read communicator content of {communicator_mp70_name}"
        communicator_json = json.loads(communicator_content)
        devCertId = communicator_json["attributes"]["devCertId"]
        assert devCertId not in [
            "NULL_CERT",
            "",
        ], f"Communicator {communicator_mp70_name} failed to create device cert"

        # step 2. create c1 whose model is 2100, expect creation of 2100 cert and update
        # certId in agency and communicator entities
        communicator_2100_name = "c1"
        local_create_communicator(
            region_name, agency_name, vehicle_name, communicator_2100_name
        )

        communicator_status, communicator_content = device_read(communicator_2100_name)
        assert (
            200 <= communicator_status < 300
        ), f"Failed to read communicator content of {communicator_mp70_name}"
        communicator_json = json.loads(communicator_content)
        devCertId = communicator_json["attributes"]["devCertId"]
        assert devCertId not in [
            "NULL_CERT",
            "",
        ], f"Communicator {communicator_2100_name} failed to create 2100 cert"

        agency_status, agency_content = agency_read(region_name, agency_name)
        assert 200 <= agency_status < 300, "Failed to read agency content"
        agency_json = json.loads(agency_content)
        Cert2100Id = agency_json["attributes"]["Cert2100Id"]
        assert (
            Cert2100Id == devCertId
        ), "Failed to update 2100 certId in the agency entity"

        local_delete_communicator(
            region_name, agency_name, vehicle_name, communicator_mp70_name
        )
        local_delete_communicator(
            region_name, agency_name, vehicle_name, communicator_2100_name
        )
        local_delete_vehicle(region_name, agency_name, vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)
