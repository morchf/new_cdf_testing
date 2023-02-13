import json
import os
from unittest.mock import patch
import ui
import shutil
import status as status_constants

# the following error message is same as what is used in the ui module
err_ok = "Ok, have a nice day."


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
        json_obj = json.loads(json_str)
        copied_files = copy_json_file(file_name, json_obj)
    else:
        print(f"{file_name} not found.")
    return json_obj, copied_files


def copy_json_file(file_name, json_obj):
    copied_json_files = []
    new_file_name = ""
    if "templateId" in json_obj and json_obj["templateId"] == "region":
        new_file_name = json_obj["name"]
        shutil.copy(file_name, f"/tmp/{new_file_name}.json")
    if "templateId" in json_obj and json_obj["templateId"] == "agency":
        new_file_name = json_obj["name"]
        shutil.copy(file_name, f"/tmp/{new_file_name}.json")
    if "templateId" in json_obj and json_obj["templateId"] == "vehicle":
        new_file_name = json_obj["deviceId"]
        shutil.copy(file_name, f"/tmp/{new_file_name}.json")
    if "templateId" in json_obj and json_obj["templateId"] == "phaseselector":
        new_file_name = json_obj["deviceId"]
        shutil.copy(file_name, f"/tmp/{new_file_name}.json")
    copied_json_files.append(f"/tmp/{new_file_name}.json")
    return copied_json_files


def remove_json_file(copied_files):
    for f in copied_files:
        os.remove(f)


class MockRegion(object):
    def __init__(self):
        self.status = ""

    def create(self, two):
        return ""

    def delete(self):
        return ""


class MockRegionWithCreation(object):
    def __init__(self):
        self.status = ""

    def create(self, two):
        self.status = status_constants.REGION_STATUS_EXISTS
        return ""


class MockRegionWithDeletion(object):
    def __init__(self):
        self.status = ""

    def delete(self):
        self.status = status_constants.REGION_STATUS_DOES_NOT_EXIST
        return ""


def test_new_region_not_exists():
    with patch("ui.Region") as mock_region:
        mock_region.return_value = MockRegion()
        mock_region.return_value.status = status_constants.REGION_STATUS_DOES_NOT_EXIST
        mock_region.return_value.http_code = 200
        mock_region.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_region(region_data["name"])
        remove_json_file(copied_file_region)
    assert not rc
    assert error == (
        f"Error: {mock_region.return_value.http_code}, "
        f"{mock_region.return_value.http_content}. r1 create status is "
        f"{mock_region.return_value.status}"
    )


def test_new_region_exists():
    with patch("ui.Region") as mock_region:
        mock_region.return_value = MockRegion()
        mock_region.return_value.status = status_constants.REGION_STATUS_EXISTS
        mock_region.return_value.http_code = 200
        mock_region.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_region(region_data["name"])
        remove_json_file(copied_file_region)
    assert not rc
    assert error == (
        f"Region {region_data['name']} already exists with status = "
        f"{mock_region.return_value.status}, no changes made"
    )


def test_new_region_created():
    with patch("ui.Region") as mock_region:
        mock_region.return_value = MockRegionWithCreation()
        mock_region.return_value.status = status_constants.REGION_STATUS_DOES_NOT_EXIST
        mock_region.return_value.http_code = 200
        mock_region.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_region(region_data["name"])
        remove_json_file(copied_file_region)
    assert rc
    assert error == err_ok


def test_new_region_json_not_exist():
    with patch("ui.Region") as mock_region:
        with patch("ui.get_json") as mock_get_json:
            mock_get_json.return_value = ""
            mock_region.return_value = MockRegion()
            mock_region.return_value.status = (
                status_constants.REGION_STATUS_DOES_NOT_EXIST
            )
            mock_region.return_value.http_code = 200
            mock_region.return_value.http_content = ""
            region_data, copied_file_region = open_json_file("TestFiles/r1.json")
            rc, error = ui.new_region(region_data["name"])
            remove_json_file(copied_file_region)
    assert not rc
    assert error == "Missing r1.json file"


def test_new_region_json_no_null_guid():
    with patch("ui.Region") as mock_region:
        with patch("ui.get_json") as mock_get_json:
            mock_region.return_value = MockRegion()
            mock_region.return_value.status = (
                status_constants.REGION_STATUS_DOES_NOT_EXIST
            )
            mock_region.return_value.http_code = 200
            mock_region.return_value.http_content = ""
            region_data, copied_file_region = open_json_file("TestFiles/r1.json")
            mock_get_json.return_value = json.dumps(region_data).replace(
                "NULL_GUID", ""
            )
            rc, error = ui.new_region(region_data["name"])
            remove_json_file(copied_file_region)
    assert not rc
    assert error == "Missing NULL_GUID in r1.json file"


def test_del_region_not_exists():
    with patch("ui.Region") as mock_region:
        mock_region.return_value = MockRegion()
        mock_region.return_value.status = status_constants.REGION_STATUS_DOES_NOT_EXIST
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.del_region(region_data["name"])
        remove_json_file(copied_file_region)
    assert not rc
    assert error == (
        f"Region {region_data['name']} does not exists with status = "
        f"{mock_region.return_value.status}, no changes made"
    )


def test_del_region_exists():
    with patch("ui.Region") as mock_region:
        mock_region.return_value = MockRegionWithDeletion()
        mock_region.return_value.status = status_constants.REGION_STATUS_EXISTS
        mock_region.return_value.http_code = 200
        mock_region.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.del_region(region_data["name"])
        remove_json_file(copied_file_region)
    assert rc
    assert (
        error
        == f"Region {region_data['name']} Delete Status = {status_constants.REGION_STATUS_DOES_NOT_EXIST}"
    )


def test_del_region_fails():
    with patch("ui.Region") as mock_region:
        mock_region.return_value = MockRegion()
        mock_region.return_value.status = status_constants.REGION_STATUS_EXISTS
        mock_region.return_value.http_code = 200
        mock_region.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.del_region(region_data["name"])
        remove_json_file(copied_file_region)
    assert not rc
    assert (
        error
        == f"Region {region_data['name']} Delete Status = {status_constants.REGION_STATUS_EXISTS}"
    )


class MockAgency(object):
    def __init__(self):
        self.status = ""

    def create(self, two):
        return ""

    def delete(self):
        return ""


class MockAgencyWithCreation(object):
    def __init__(self):
        self.status = ""

    def create(self, two):
        self.status = status_constants.AGENCY_STATUS_EXISTS
        return ""


class MockAgencyWithDeletion(object):
    def __init__(self):
        self.status = ""

    def delete(self):
        self.status = status_constants.AGENCY_STATUS_DOES_NOT_EXIST
        return ""


def test_new_agency_not_exists():
    with patch("ui.Agency") as mock_agency:
        mock_agency.return_value = MockAgency()
        mock_agency.return_value.status = status_constants.AGENCY_STATUS_DOES_NOT_EXIST
        mock_agency.return_value.http_code = 200
        mock_agency.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.new_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert not rc
    assert error == (
        f"Error: {mock_agency.return_value.http_code}, "
        f"{mock_agency.return_value.http_content}. a1 create status "
        f"is {mock_agency.return_value.status}"
    )


def test_new_agency_exists():
    with patch("ui.Agency") as mock_agency:
        mock_agency.return_value = MockAgency()
        mock_agency.return_value.status = status_constants.AGENCY_STATUS_EXISTS
        mock_agency.return_value.http_code = 200
        mock_agency.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.new_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert not rc
    assert error == (
        f"Agency {agency_data['name']} already exists with status = "
        f"{mock_agency.return_value.status}, no changes made"
    )


def test_new_agency_created():
    with patch("ui.Agency") as mock_agency:
        mock_agency.return_value = MockAgencyWithCreation()
        mock_agency.return_value.status = status_constants.AGENCY_STATUS_DOES_NOT_EXIST
        mock_agency.return_value.http_code = 200
        mock_agency.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.new_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert rc
    assert error == err_ok


def test_new_agency_json_not_exist():
    with patch("ui.get_json") as mock_get_json:
        mock_get_json.return_value = ""
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert not rc
    assert error == "Missing a1.json file"


def test_new_agency_json_no_null_guid():
    with patch("ui.get_json") as mock_get_json:
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        mock_get_json.return_value = json.dumps(agency_data).replace("NULL_GUID", "")
        rc, error = ui.new_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert not rc
    assert error == "Missing NULL_GUID in a1.json file"


def test_del_agency_not_exists():
    with patch("ui.Agency") as mock_agency:
        mock_agency.return_value = MockAgency()
        mock_agency.return_value.status = status_constants.AGENCY_STATUS_DOES_NOT_EXIST
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.del_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_region)
    assert not rc
    assert error == (
        f"Agency {agency_data['name']} does not exists with status = "
        f"{mock_agency.return_value.status}, no changes made"
    )


def test_del_agency_exists():
    with patch("ui.Agency") as mock_agency:
        mock_agency.return_value = MockAgencyWithDeletion()
        mock_agency.return_value.status = status_constants.AGENCY_STATUS_EXISTS
        mock_agency.return_value.http_code = 200
        mock_agency.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.del_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert rc
    assert (
        error
        == f"Agency {agency_data['name']} Delete Status = {status_constants.AGENCY_STATUS_DOES_NOT_EXIST}"
    )


def test_del_agency_fails():
    with patch("ui.Agency") as mock_agency:
        mock_agency.return_value = MockAgency()
        mock_agency.return_value.status = status_constants.AGENCY_STATUS_EXISTS
        mock_agency.return_value.http_code = 200
        mock_agency.return_value.http_content = ""
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.del_agency(region_data["name"], agency_data["name"])
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
    assert not rc
    assert (
        error
        == f"Agency {agency_data['name']} Delete Status = {status_constants.AGENCY_STATUS_EXISTS}"
    )


class MockDevice(object):
    def __init__(self):
        self.status = ""

    def create(self, two):
        return ""

    def delete(self):
        return ""


class MockDeviceWithCreation(object):
    def __init__(self):
        self.status = ""

    def create(self, two):
        self.status = status_constants.DEVICE_STATUS_EXISTS
        return ""


class MockDeviceWithDeletion(object):
    def __init__(self):
        self.status = ""

    def delete(self):
        self.status = status_constants.DEVICE_STATUS_DOES_NOT_EXIST
        return ""


def test_new_device_not_exists():
    with patch("ui.Phaseselector") as mock_device:
        mock_device.return_value = MockDevice()
        mock_device.return_value.status = status_constants.DEVICE_STATUS_DOES_NOT_EXIST
        mock_device.return_value.http_code = 200
        mock_device.return_value.http_content = ""
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_device)
    assert not rc
    assert error == (
        f"Error: {mock_device.return_value.http_code}, "
        f"{mock_device.return_value.http_content}. ps1 create status "
        f"is {mock_device.return_value.status}"
    )


def test_new_device_exists():
    with patch("ui.Phaseselector") as mock_device:
        mock_device.return_value = MockDevice()
        mock_device.return_value.status = status_constants.DEVICE_STATUS_EXISTS
        mock_device.return_value.http_code = 200
        mock_device.return_value.http_content = ""
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_device)
    assert not rc
    assert error == (
        f"Agency {agency_data['name']} does not exist or phaseselector "
        f"{device_data['deviceId']} already exists. No changes made"
    )


def test_new_device_created():
    with patch("ui.Phaseselector") as mock_device:
        mock_device.return_value = MockDeviceWithCreation()
        mock_device.return_value.status = status_constants.DEVICE_STATUS_DOES_NOT_EXIST
        mock_device.return_value.http_code = 200
        mock_device.return_value.http_content = ""
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.new_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_device)
    assert rc
    assert error == err_ok


def test_new_device_json_not_exist():
    with patch("ui.get_json") as mock_get_json:
        mock_get_json.return_value = ""
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.new_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_device)
    assert not rc
    assert error == "Missing ps1.json file"


def test_del_device_not_exists():
    with patch("ui.Phaseselector") as mock_device:
        mock_device.return_value = MockDevice()
        mock_device.return_value.status = status_constants.DEVICE_STATUS_DOES_NOT_EXIST
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        rc, error = ui.del_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_device)
    assert not rc
    assert error == (
        f"Phase selector {device_data['deviceId']} in Agency {agency_data['name']} "
        f"does not exist or does not have cert. Status = "
        f"{mock_device.return_value.status}. No changes made"
    )


def test_del_device_exists():
    with patch("ui.Phaseselector") as mock_device:
        mock_device.return_value = MockDeviceWithDeletion()
        mock_device.return_value.status = status_constants.DEVICE_STATUS_EXISTS
        mock_device.return_value.http_code = 200
        mock_device.return_value.http_content = ""
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.del_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_device)
    assert rc
    assert (
        error
        == f"Phase selector {device_data['deviceId']} Status = {status_constants.DEVICE_STATUS_DOES_NOT_EXIST}"
    )


def test_del_device_fails():
    with patch("ui.Phaseselector") as mock_device:
        mock_device.return_value = MockDevice()
        mock_device.return_value.status = status_constants.DEVICE_STATUS_EXISTS
        mock_device.return_value.http_code = 200
        mock_device.return_value.http_content = ""
        device_data, copied_file_device = open_json_file("TestFiles/ps1.json")
        region_data, copied_file_region = open_json_file("TestFiles/r1.json")
        agency_data, copied_file_agency = open_json_file("TestFiles/a1.json")
        rc, error = ui.del_phaseselector(
            region_data["name"], agency_data["name"], device_data["deviceId"]
        )
        remove_json_file(copied_file_region)
        remove_json_file(copied_file_agency)
        remove_json_file(copied_file_device)
    assert not rc
    assert (
        error
        == f"Phase selector {device_data['deviceId']} Status = {status_constants.DEVICE_STATUS_EXISTS}"
    )


def test_list_regions():
    with patch("ui.alib.list_all_regions") as mock_list_regions:
        mocked_list_all_regions_content = (
            b'{"results":[{"attributes":{"caCertId":"NULL_CA",'
            b'"regionGUID":"NULL_GUID","regionDNS":"1.7.2.8"},"category":"group",'
            b'"templateId":"region","parentPath":"/","name":"test_region",'
            b'"description":"uniqueness test region","groupPath":"/test_region",'
            b'"relation":"parent","direction":"in"}]}'
        )
        mocked_region_list = [
            {
                "attributes": {
                    "caCertId": "NULL_CA",
                    "regionGUID": "NULL_GUID",
                    "regionDNS": "1.7.2.8",
                },
                "category": "group",
                "templateId": "region",
                "parentPath": "/",
                "name": "test_region",
                "description": "uniqueness test region",
                "groupPath": "/test_region",
                "relation": "parent",
                "direction": "in",
            }
        ]
        mock_list_regions.return_value = (200, mocked_list_all_regions_content)
        rc, region_list_array = ui.list_regions()
        assert rc
        assert region_list_array == mocked_region_list


def test_list_regions_failed_datatype():
    with patch("ui.alib.list_all_regions") as mock_list_regions:
        mocked_list_all_regions_content = b'{"results":""}'
        mocked_region_list = ""
        mock_list_regions.return_value = (200, mocked_list_all_regions_content)
        rc, region_list_array = ui.list_regions()
        assert not rc
        assert region_list_array == mocked_region_list


def test_list_regions_failed_not_found():
    with patch("ui.alib.list_all_regions") as mock_list_regions:
        mocked_list_all_regions_content = []
        mock_list_regions.return_value = (404, mocked_list_all_regions_content)
        rc, region_list_array = ui.list_regions()
        assert not rc
        assert region_list_array == mocked_list_all_regions_content


def test_list_agencies():
    with patch("ui.alib.list_all_agencies_in_region") as mock_list_agencies:
        mocked_list_all_agencies_content = (
            b'{"results":[{"attributes":{"city":"Orlando",'
            b'"timezone":"Central","agencyID":"NULL_GUID","agencyCode":234,'
            b'"priority":"High","vpsCertId":"NULL_CERT","caCertId":"NULL_CA",'
            b'"state":"FL"}, "category":"group","templateId":"agency",'
            b'"parentPath":"/test_region","description":"uniqueness test agency", '
            b'"name":"test_agency","groupPath":"/test_region/test_agency",'
            b'"relation":"parent","direction":"in"}]}'
        )
        mocked_agencies_list = [
            {
                "attributes": {
                    "city": "Orlando",
                    "timezone": "Central",
                    "agencyID": "NULL_GUID",
                    "agencyCode": 234,
                    "priority": "High",
                    "vpsCertId": "NULL_CERT",
                    "caCertId": "NULL_CA",
                    "state": "FL",
                },
                "category": "group",
                "templateId": "agency",
                "parentPath": "/test_region",
                "description": "uniqueness test agency",
                "name": "test_agency",
                "groupPath": "/test_region/test_agency",
                "relation": "parent",
                "direction": "in",
            }
        ]
        mock_list_agencies.return_value = (200, mocked_list_all_agencies_content)
        rc, agency_list_array = ui.list_agencies("test_region")
        assert rc
        assert agency_list_array == mocked_agencies_list


def test_list_agencies_failed_datatype():
    with patch("ui.alib.list_all_agencies_in_region") as mock_list_agencies:
        mocked_list_all_agencies_content = b'{"results":""}'
        mocked_agencies_list = ""
        mock_list_agencies.return_value = (200, mocked_list_all_agencies_content)
        rc, agency_list_array = ui.list_agencies("test_region")
        assert not rc
        assert agency_list_array == mocked_agencies_list


def test_list_agencies_failed_not_found():
    with patch("ui.alib.list_all_agencies_in_region") as mock_list_agencies:
        mocked_list_all_agencies_content = []
        mock_list_agencies.return_value = (404, mocked_list_all_agencies_content)
        rc, agency_list_array = ui.list_agencies("test_region")
        assert not rc
        assert agency_list_array == mocked_list_all_agencies_content


def test_list_devices():
    with patch("ui.alib.list_all_devices_in_agency") as mock_list_devices:
        mocked_list_all_devices_content = (
            b'{"results":[{"attributes":{"city":"Orlando",'
            b'"timezone":"Central","agencyID":"NULL_GUID","agencyCode":234,'
            b'"priority":"High","vpsCertId":"NULL_CERT","caCertId":"NULL_CA",'
            b'"state":"FL"}, "category":"group","templateId":"agency",'
            b'"parentPath":"/test_region","description":"uniqueness test agency", '
            b'"name":"test_agency","groupPath":"/test_region/test_agency",'
            b'"relation":"parent","direction":"in"}]}'
        )
        mocked_devices_list = [
            {
                "attributes": {
                    "city": "Orlando",
                    "timezone": "Central",
                    "agencyID": "NULL_GUID",
                    "agencyCode": 234,
                    "priority": "High",
                    "vpsCertId": "NULL_CERT",
                    "caCertId": "NULL_CA",
                    "state": "FL",
                },
                "category": "group",
                "templateId": "agency",
                "parentPath": "/test_region",
                "description": "uniqueness test agency",
                "name": "test_agency",
                "groupPath": "/test_region/test_agency",
                "relation": "parent",
                "direction": "in",
            }
        ]
        mock_list_devices.return_value = (200, mocked_list_all_devices_content)
        rc, devices_list_array = ui.list_devices("test_region", "test_agency")
        assert rc
        assert devices_list_array == mocked_devices_list


def test_list_devices_failed_datatype():
    with patch("ui.alib.list_all_devices_in_agency") as mock_list_devices:
        mocked_list_all_devices_content = b'{"results":""}'
        mocked_devices_list = ""
        mock_list_devices.return_value = (200, mocked_list_all_devices_content)
        rc, devices_list_array = ui.list_devices("test_region", "test_agency")
        assert not rc
        assert devices_list_array == mocked_devices_list


def test_list_devices_failed_not_found():
    with patch("ui.alib.list_all_devices_in_agency") as mock_list_devices:
        mocked_list_all_devices_content = []
        mock_list_devices.return_value = (404, mocked_list_all_devices_content)
        rc, devices_list_array = ui.list_devices("test_region", "test_agency")
        assert not rc
        assert devices_list_array == mocked_list_all_devices_content
