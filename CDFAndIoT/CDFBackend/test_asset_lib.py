"""
    test_asset_lib.py provides a test frame work for asset_lib.py.
    Test cases are create, delete, list, write to entities using agency template.
    Test cases are create, delete, list, write to entities using vehicle template.
    The agency for a vehicle must be created first. The vehicle json file identifies
    which agency it is being create under.
    All tests leave the asset library in the same state as before starting the test,
    meaning if an agency is created then that agency is deleted.
"""
import pytest
import os
import random
import json
import asset_lib as alib

debug = False
region_write_json_str = '{{ "attributes": {{ "caCertId": "{}" }} }}'
agency_write_json_str = '{{ "attributes": {{ "caCertId": "{}" }} }}'
vehicle_write_json_str = '{{ "attributes": {{ "uniqueId": "{}" }} }}'


def file_check(name):
    return os.path.exists(f"/tmp/{name}.json")


def response_ok(rc):
    return rc in [200, 201, 202, 204]


def local_create_communicator(communicator_name):
    rc = file_check(communicator_name)
    assert rc, f"Abort test. Need .json files {communicator_name}"

    with open(f"/tmp/{communicator_name}.json") as communicator_file:
        communicator_json_str = communicator_file.read()
    communicator_json_str = communicator_json_str.replace("\r", "").replace("\n", "")

    rc, _ = alib.device_create(communicator_json_str)
    assert response_ok(rc), f"failed create_communicator({rc})"


def local_delete_communicator(communicator_name):
    rc, _ = alib.device_delete(communicator_name)
    assert response_ok(rc), f"failed delete_communicator({rc})"


def local_create_vehicle(vehicle_name):
    rc = file_check(vehicle_name)
    assert rc, f"Abort test. Need .json files {vehicle_name}"

    with open(f"/tmp/{vehicle_name}.json") as vehicle_file:
        vehicle_json_str = vehicle_file.read()
    vehicle_json_str = vehicle_json_str.replace("\r", "").replace("\n", "")

    rc, _ = alib.device_create(vehicle_json_str)
    assert response_ok(rc), f"failed create_vehicle({rc})"


def local_delete_vehicle(vehicle_name):
    rc, _ = alib.device_delete(vehicle_name)
    assert response_ok(rc), f"failed delete_vehicle({rc})"


def local_create_agency(agency_name):
    rc = file_check(agency_name)
    assert rc, f"Abort test. Need .json files for {agency_name}"

    with open(f"/tmp/{agency_name}.json") as agency_file:
        agency_json_str = agency_file.read()
    agency_json_str = agency_json_str.replace("\r", "").replace("\n", "")

    rc, _ = alib.agency_create(agency_name, agency_json_str)
    assert response_ok(rc), f"failed create_agency({rc})"


def local_delete_agency(region_name, agency_name):
    rc, _ = alib.agency_delete(region_name, agency_name)
    assert response_ok(rc), f"failed delete_agency({rc})"


def local_create_region(region_name):
    rc = file_check(region_name)
    assert rc, f"Abort test. Need .json files for {region_name}"

    with open(f"/tmp/{region_name}.json") as region_file:
        region_json_str = region_file.read()
    region_json_str = region_json_str.replace("\r", "").replace("\n", "")

    rc, _ = alib.region_create(region_name, region_json_str)
    assert response_ok(rc), f"failed create_region({rc})"


def local_delete_region(region_name):
    rc, _ = alib.region_delete(region_name)
    assert response_ok(rc), f"failed delete_region({rc})"


class TestAssetLib:
    @pytest.fixture(scope="function", autouse=True)
    def tearDown(self):
        # Delete all entities here. Failed test does not
        # delete entities created for test
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        communicator_name = "c1"
        alib.region_delete(region_name)
        alib.agency_delete(region_name, agency_name)
        alib.device_delete(vehicle_name)
        alib.device_delete(communicator_name)

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

    def test_region_agency(self):
        region_name = "r1"
        agency_name = "a1"
        local_create_region(region_name)
        local_create_agency(agency_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Create CA agency, create vehicle, delete vehicle, delete agency
    """

    def test_region_agency_vehicle(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        local_create_region(region_name)
        local_create_agency(agency_name)
        local_create_vehicle(vehicle_name)
        local_delete_vehicle(vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    """
        Write then Read region, agency & vehicle.
    """

    def test_write_read(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        local_create_region(region_name)
        local_create_agency(agency_name)
        local_create_vehicle(vehicle_name)

        # Generate random cert_id to verify test is successful
        region_random_num = random.randint(1, 1000000)
        region_test_write_json_str = region_write_json_str.format(region_random_num)
        agency_random_num = random.randint(1, 1000000)
        agency_test_write_json_str = agency_write_json_str.format(agency_random_num)
        vehicle_random_num = random.randint(1, 1000000)
        vehicle_test_write_json_str = vehicle_write_json_str.format(vehicle_random_num)

        # Writes
        rc, _ = alib.region_write(region_name, region_test_write_json_str)
        assert response_ok(rc), f"test_write_read(): failed region_write({rc})"

        rc, _ = alib.agency_write(region_name, agency_name, agency_test_write_json_str)
        assert response_ok(rc), f"test_write_read(): failed agency_write({rc})"

        rc, _ = alib.device_write(vehicle_name, vehicle_test_write_json_str)
        assert response_ok(rc), f"test_write_read(): failed device_write({rc})"

        # Reads
        rc, read_region_content = alib.region_read(region_name)
        assert response_ok(rc), f"test_write_read(): failed region_read({rc})"

        rc, read_agency_content = alib.agency_read(region_name, agency_name)
        assert response_ok(rc), f"test_write_read(): failed agency_read({rc})"

        rc, read_vehicle_content = alib.device_read(vehicle_name)
        assert response_ok(rc), f"test_write_read(): failed device_read({rc})"

        # Verify read matches write
        region_content_json_obj = json.loads(read_region_content)
        agency_content_json_obj = json.loads(read_agency_content)
        vehicle_content_json_obj = json.loads(read_vehicle_content)

        assert isinstance(
            region_content_json_obj, dict
        ), "test_write_read(): failed region_content_json_obj"
        assert isinstance(
            agency_content_json_obj, dict
        ), "test_write_read(): failed agency_content_json_obj"
        assert isinstance(
            vehicle_content_json_obj, dict
        ), "test_write_read(): failed vehicle_content_json_obj"

        region_attributes_json_obj = region_content_json_obj.get("attributes", None)
        agency_attributes_json_obj = agency_content_json_obj.get("attributes", None)
        vehicle_attributes_json_obj = vehicle_content_json_obj.get("attributes", None)

        assert isinstance(
            region_attributes_json_obj, dict
        ), "test_write_read(): failed region_attributes_json_obj"
        assert isinstance(
            agency_attributes_json_obj, dict
        ), "test_write_read(): failed agency_attributes_json_obj"
        assert isinstance(
            vehicle_attributes_json_obj, dict
        ), "test_write_read(): failed vehicle_attributes_json_obj"

        compare_ca_cert_id = int(agency_attributes_json_obj.get("caCertId", "0"))
        compare_dev_cert_id = int(vehicle_attributes_json_obj.get("uniqueId", "0"))

        assert (
            compare_ca_cert_id == agency_random_num
        ), "test_write_read(): ca_cert_id read/write value does not match"
        assert (
            compare_dev_cert_id == vehicle_random_num
        ), "test_write_read(): dev_cert_id read/write value does not match"

        # Read value matches the value written!! SUCCESS!!

        # Now delete region, vehicle and agency
        local_delete_vehicle(vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_list_devices_within_an_agency(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        local_create_region(region_name)
        local_create_agency(agency_name)
        local_create_vehicle(vehicle_name)

        rc, list_all_devices_content = alib.list_all_devices_in_agency(
            region_name, agency_name
        )
        assert response_ok(
            rc
        ), f"test_list_devices_within_an_agency(): failed list_all_devices_in_agency({rc})"

        list_all_devices_json_obj = json.loads(list_all_devices_content)
        assert isinstance(
            list_all_devices_json_obj, dict
        ), "test_list_devices_within_an_agency(): failed list_all_devices_json_obj"

        device_list_array = list_all_devices_json_obj.get("results", None)
        assert isinstance(
            device_list_array, list
        ), "test_list_devices_within_an_agency(): failed list_all_devices_json_obj"

        found = False
        for device in device_list_array:
            device_id = device.get("deviceId", None)
            if device_id == vehicle_name:
                found = True
                break
        else:
            assert (
                found
            ), "test_list_devices_within_an_agency(): did not find agency or vehicle in the list"

        # Now delete vehicle and agency
        local_delete_vehicle(vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_list_agencies_within_a_region(self):
        region_name = "r1"
        agency_name = "a1"
        local_create_region(region_name)
        local_create_agency(agency_name)

        rc, list_all_agencies_content = alib.list_all_agencies_in_region(region_name)
        assert response_ok(
            rc
        ), f"test_list_agencies_within_a_region(): failed test_list_agencies_within_a_region({rc})"

        list_all_agencies_json_obj = json.loads(list_all_agencies_content)
        assert isinstance(
            list_all_agencies_json_obj, dict
        ), "test_list_agencies_within_a_region(): failed list_all_agencies_json_obj"

        agency_list_array = list_all_agencies_json_obj.get("results", None)
        assert isinstance(
            agency_list_array, list
        ), "test_list_agencies_within_a_region(): failed list_all_agencies_json_obj"

        found = False
        for agency in agency_list_array:
            name = agency.get("name", None)
            if name == agency_name:
                found = True
                break
        else:
            assert (
                found
            ), "test_list_agencies_within_a_region(): did not find agency in the list"

        # Now delete region and agency
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_list_regions(self):
        region_name = "r1"
        local_create_region(region_name)

        rc, list_all_regions_content = alib.list_all_regions()
        assert response_ok(rc), f"test_list_regions(): failed test_list_regions({rc})"

        list_all_regions_json_obj = json.loads(list_all_regions_content)
        assert isinstance(
            list_all_regions_json_obj, dict
        ), "test_list_regions(): failed list_all_regions_json_obj"

        region_list_array = list_all_regions_json_obj.get("results", None)
        assert isinstance(
            region_list_array, list
        ), "test_list_regions(): failed region_list_array"

        found = False
        for region in region_list_array:
            name = region.get("name", None)
            if name == region_name:
                found = True
                break
        else:
            assert found, "test_list_regions(): did not find region in the list"

        # Now delete region
        local_delete_region(region_name)

    def test_failed_validation_region(self):
        region_name = "r1_fv"

        rc = file_check(region_name)
        assert rc, f"Abort test. Need .json files for {region_name}"

        with open(f"/tmp/{region_name}.json") as region_file:
            region_json_str = region_file.read()
        region_json_str = region_json_str.replace("\r", "").replace("\n", "")

        rc, content = alib.region_create(region_name, region_json_str)
        print(content)
        assert (
            content == b'{"error":"FAILED_VALIDATION"}'
        ), f"Region create did not fail validation as expected. Content is {content}"
        assert (
            rc == 400
        ), f"region create did not fail validation as expected. Status code is {rc}"

    def test_failed_validation_agency(self):
        region_name = "r1"
        agency_name = "a1_fv"
        local_create_region(region_name)

        rc = file_check(agency_name)
        assert rc, f"Abort test. Need .json files for {agency_name}"

        with open(f"/tmp/{agency_name}.json") as agency_file:
            agency_json_str = agency_file.read()
        agency_json_str = agency_json_str.replace("\r", "").replace("\n", "")

        rc, content = alib.agency_create(agency_name, agency_json_str)
        assert (
            content == b'{"error":"FAILED_VALIDATION"}'
        ), f"Agency create did not fail validation as expected. Content is {content}"
        assert (
            rc == 400
        ), f"Agency create did not fail validation as expected. Status code is {rc}"

        # clean up
        local_delete_region(region_name)

    def test_failed_validation_vehicle(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1_fv"
        local_create_region(region_name)
        local_create_agency(agency_name)

        rc = file_check(vehicle_name)
        assert rc, f"Abort test. Need .json files {vehicle_name}"

        with open(f"/tmp/{vehicle_name}.json") as vehicle_file:
            vehicle_json_str = vehicle_file.read()
        vehicle_json_str = vehicle_json_str.replace("\r", "").replace("\n", "")

        rc, content = alib.device_create(vehicle_json_str)
        assert (
            content == b'{"error":"FAILED_VALIDATION"}'
        ), f"Vehicle create did not fail validation as expected. Content is {content}"
        assert (
            rc == 400
        ), f"Vehicle create did not fail validation as expected. Status code is {rc}"

        # Now delete agency and region
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_invalid_relation_vehicle(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1_ir"
        local_create_region(region_name)
        local_create_agency(agency_name)

        rc = file_check(vehicle_name)
        assert rc, f"Abort test. Need .json files {vehicle_name}"

        with open(f"/tmp/{vehicle_name}.json") as vehicle_file:
            vehicle_json_str = vehicle_file.read()
        vehicle_json_str = vehicle_json_str.replace("\r", "").replace("\n", "")

        rc, content = alib.device_create(vehicle_json_str)
        assert (
            content == b'{"error":"INVALID_RELATION"}'
        ), f"Vehicle create did not have an invalid relation as expected. Content is {content}"
        assert (
            rc == 400
        ), f"Vehicle create did not have an invalid relation as expected. Status code is {rc}"

        # Now delete region and agency
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_failed_validation_phase_selector(self):
        region_name = "r1"
        agency_name = "a1"
        ps_name = "ps1_fv"
        local_create_region(region_name)
        local_create_agency(agency_name)

        rc = file_check(ps_name)
        assert rc, f"Abort test. Need .json files {ps_name}"

        with open(f"/tmp/{ps_name}.json") as ps_file:
            ps_json_str = ps_file.read()
        ps_json_str = ps_json_str.replace("\r", "").replace("\n", "")

        rc, content = alib.device_create(ps_json_str)
        assert (
            content == b'{"error":"FAILED_VALIDATION"}'
        ), f"Phase selector create did not fail validation as expected. Content is {content}"
        assert (
            rc == 400
        ), f"Phase selector create did not fail validation as expected. Status code is {rc}"

        # Now delete vehicle and agency
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_invalid_relation_phase_selector(self):
        region_name = "r1"
        agency_name = "a1"
        ps_name = "ps1_ir"
        local_create_region(region_name)
        local_create_agency(agency_name)

        rc = file_check(ps_name)
        assert rc, f"Abort test. Need .json files {ps_name}"

        with open(f"/tmp/{ps_name}.json") as ps_file:
            ps_json_str = ps_file.read()
        ps_json_str = ps_json_str.replace("\r", "").replace("\n", "")

        rc, content = alib.device_create(ps_json_str)
        assert (
            content == b'{"error":"INVALID_RELATION"}'
        ), f"Phase selector create did not have an invalid relation as expected. Content is {content}"
        assert (
            rc == 400
        ), f"Phase selector create did not have an invalid relation as expected. Status code is {rc}"

        # Now delete region and agency
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)

    def test_associate_list_disociate_communicators_in_vehicle(self):
        region_name = "r1"
        agency_name = "a1"
        vehicle_name = "v1"
        communicator_name = "c1"
        local_create_region(region_name)
        local_create_agency(agency_name)
        local_create_vehicle(vehicle_name)
        local_create_communicator(communicator_name)

        # Associate communicator from vehicle
        rc, communicator_associate_content = alib.communicator_associate(
            communicator_name, vehicle_name
        )
        assert response_ok(
            rc
        ), f"test_associate_list_disociate_communicators_in_vehicle(): failed communicator_associate({rc})"

        # List communicators in vehicle and check communicator c1 is in the list
        rc, list_all_communicators_content = alib.list_all_communicators_in_vehicle(
            vehicle_name
        )
        assert response_ok(
            rc
        ), f"test_associate_list_disociate_communicators_in_vehicle(): failed test_list_all_communicators_in_vehicle({rc})"

        list_all_communicators_json_obj = json.loads(list_all_communicators_content)
        assert isinstance(
            list_all_communicators_json_obj, dict
        ), "test_associate_list_disociate_communicators_in_vehicle(): failed list_all_communicators_json_obj"

        communicator_list_array = list_all_communicators_json_obj.get("results", None)
        assert isinstance(
            communicator_list_array, list
        ), "test_associate_list_disociate_communicators_in_vehicle(): failed list_all_communicators_json_obj"

        found = False
        for communicator in communicator_list_array:
            name = communicator.get("deviceId", None)
            if name == communicator_name:
                found = True
                break
        else:
            assert (
                found
            ), "test_associate_list_disociate_communicators_in_vehicle(): did not find communicator in the list"

        # Disociate communicator from vehicle
        rc, communicator_disociate_content = alib.communicator_disociate(
            communicator_name, vehicle_name
        )
        assert response_ok(
            rc
        ), f"test_associate_list_disociate_communicators_in_vehicle(): failed communicator_disociate({rc})"

        # List communicators in vehicle again and check communicator c1 is no longer in the list
        rc, list_all_communicators_content = alib.list_all_communicators_in_vehicle(
            vehicle_name
        )
        assert response_ok(
            rc
        ), f"test_associate_list_disociate_communicators_in_vehicle(): failed test_list_all_communicators_in_vehicle({rc})"

        list_all_communicators_json_obj = json.loads(list_all_communicators_content)
        assert isinstance(
            list_all_communicators_json_obj, dict
        ), "test_associate_list_disociate_communicators_in_vehicle(): failed list_all_communicators_json_obj"

        communicator_list_array = list_all_communicators_json_obj.get("results", None)
        assert isinstance(
            communicator_list_array, list
        ), "test_associate_list_disociate_communicators_in_vehicle(): failed list_all_communicators_json_obj"
        assert (
            communicator_list_array == []
        ), "test_associate_list_disociate_communicators_in_vehicle(): find communicator in the listj"
        # Now delete region and agency
        local_delete_communicator(communicator_name)
        local_delete_vehicle(vehicle_name)
        local_delete_agency(region_name, agency_name)
        local_delete_region(region_name)
