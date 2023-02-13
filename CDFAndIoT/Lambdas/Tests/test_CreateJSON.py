import json
import os
import sys
import shutil

sys.path.append(
    os.path.join(
        os.path.abspath(os.path.realpath(__file__) + 2 * "/.."),
        "CreateJSON",
        "lambda-code",
    )
)
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 2 * "/.."), "CDFBackend")
)

import CreateJSON as create_json  # noqa: E402

from ui import (  # noqa: E402
    new_region,
    del_region,
    new_agency,
    del_agency,
    new_device,
    del_device,
)


class TestCreateJSON:

    # the json files need to be copied to the /tmp directory, as Lambda is only
    # allowed to write to the /tmp folder
    def copy_json_file(self, file_name, json_obj):
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

    def remove_json_file(self, copied_files):
        for f in copied_files:
            os.remove(f)

    def open_json_file(self, file_name):
        json_str = None
        json_obj = None
        copied_files = []
        if os.path.exists(file_name):
            with open(f"{file_name}", "r") as f:
                json_str = f.read()
            json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
            json_obj = json.loads(json_str)
            copied_files = self.copy_json_file(file_name, json_obj)
        else:
            print(f"{file_name} not found.")

        return json_obj, copied_files

    def test_check_unique_region(self):
        # region uniqueness check
        region_data, copied_files = self.open_json_file("test_region.json")
        rc, error = create_json.check_unique_group(region_data, ["regionDNS", "name"])
        assert rc == True, f"{error}"  # noqa: E712
        # create new region and recheck uniqueness
        rc_new_region, error_new_region = new_region(region_data["name"])
        rc_again, error = create_json.check_unique_group(
            region_data, ["regionDNS", "name"]
        )
        assert rc_again == False, f"{error}"  # noqa: E712
        error_list = [
            "error regionDNS already exists in region",
            "error name already exists in region",
        ]
        assert error in error_list

        # clean up
        del_region(region_data["name"])
        self.remove_json_file(copied_files)

    def test_check_unique_agency(self):
        # region uniqueness check
        region_data, copied_region_files = self.open_json_file("test_region1.json")
        rc, error = create_json.check_unique_group(region_data, ["regionDNS", "name"])
        assert rc == True, f"{error}"  # noqa: E712
        # create new region and recheck uniqueness
        rc_new_region, error_new_region = new_region(region_data["name"])

        # agency uniqueness check
        agency_data, copied_agency_files = self.open_json_file("test_agency1.json")
        rc, error = create_json.check_unique_group(agency_data, ["agencyCode", "name"])
        assert rc == True, f"{error}"  # noqa: E712

        # create new agency and recheck uniqueness
        new_agency(region_data["name"], agency_data["name"])
        rc_again, error = create_json.check_unique_group(
            agency_data, ["agencyCode", "name"]
        )
        assert rc_again == False, f"{error}"  # noqa: E712
        error_list = [
            "error agencyCode already exists in agency",
            "error agencyID already exists in agency",
            "error name already exists in agency",
        ]
        assert error in error_list
        del_agency(region_data["name"], agency_data["name"])
        del_region(region_data["name"])
        self.remove_json_file(copied_region_files)
        self.remove_json_file(copied_agency_files)

    def test_check_unique_vehicle_device(self):

        # region uniqueness check
        region_data, copied_region_files = self.open_json_file("test_region2.json")
        rc, error = create_json.check_unique_group(region_data, ["regionDNS", "name"])
        assert rc == True, f"{error}"  # noqa: E712
        # create new region and recheck uniqueness
        rc_new_region, error_new_region = new_region(region_data["name"])

        # agency uniqueness check
        agency_data, copied_agency_files = self.open_json_file("test_agency2.json")
        rc, error = create_json.check_unique_group(agency_data, ["agencyCode", "name"])
        assert rc == True, f"{error}"  # noqa: E712

        # create new agency and recheck uniqueness
        new_agency(region_data["name"], agency_data["name"])

        # vehicle uniqueness check
        vehicle_device_data, copied_vehicle_files = self.open_json_file(
            "test_vehicle2.json"
        )
        unique_list_veh = [
            "gttSerial",
            "addressMAC",
            "addressLAN",
            "addressWAN",
            "IMEI",
            "VID",
        ]
        rc, error = create_json.check_unique_device(
            vehicle_device_data, unique_list_veh
        )
        assert rc == True, f"{error}"  # noqa: E712

        # create new vehicle and recheck uniqueness
        new_device(
            region_data["name"], agency_data["name"], vehicle_device_data["deviceId"]
        )
        rc_again, error = create_json.check_unique_device(
            vehicle_device_data, unique_list_veh
        )
        assert rc_again == False, f"{error}"  # noqa: E712
        error_list = [
            "error " + name + " already exists in device" for name in unique_list_veh
        ]
        assert error in error_list

        # clean up vehicle entity
        del_device(
            region_data["name"], agency_data["name"], vehicle_device_data["deviceId"]
        )
        del_agency(region_data["name"], agency_data["name"])
        del_region(region_data["name"])
        self.remove_json_file(copied_region_files)
        self.remove_json_file(copied_agency_files)
        self.remove_json_file(copied_vehicle_files)

    def test_get_modem_data(self):
        # Check for data retrieval with valid SN
        serialNumber = "N684570206021035"
        data = create_json.get_modem_data(serialNumber)
        assert data is not None

        # Check for no data retrieval with invalid SN
        serialNumber = "blah"
        data = create_json.get_modem_data(serialNumber)
        assert data == []

    def test_determine_MP70_data(self):
        # Checks if codes succeeds with actual device
        serialNumber = "N684570206021035"
        get_data = create_json.get_modem_data(serialNumber)

        entity_dict = {
            "addressMAC": "00:14:3E:43:68:F5",
            "addressWAN": "10.2.3.1",
            "IMEI": "358000000000000",
            "model": "MP-70",
        }

        MP70_data = create_json.determine_MP70_data(entity_dict, get_data)
        assert MP70_data is not None
        assert MP70_data[0] == entity_dict["addressMAC"]

        # Checks if code succeeds when there is a simulated device
        # (no valid serial number)
        serialNumber = "blah"
        get_data = create_json.get_modem_data(serialNumber)

        entity_dict = {
            "addressMAC": "03:94:02:88:02:34",
            "addressWAN": "10.2.3.1",
            "IMEI": "358000000000000",
            "model": "MP-70",
        }

        MP70_data = create_json.determine_MP70_data(entity_dict, get_data)
        assert MP70_data is not None
        assert MP70_data[0] == entity_dict["addressMAC"]

    def test_lambda_handler(self):
        # Check region json creation
        data, _ = self.open_json_file("test_region_input.json")
        region_data = create_json.lambda_handler(data["input"], None)
        assert region_data is not None

        # Check agency json creation
        data, _ = self.open_json_file("test_agency_input.json")
        agency_data = create_json.lambda_handler(data["input"], None)
        assert agency_data is not None

        # Check device json creation
        data, _ = self.open_json_file("test_device_input.json")
        device_data = create_json.lambda_handler(data["input"], None)
        assert device_data is not None
