import json
import os
import sys
import shutil
import urllib3

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
    new_communicator,
    del_communicator,
)

http = urllib3.PoolManager()


class TestCreateJSON:

    # the json files need to be copied to the /tmp directory, as Lambda is only
    # allowed to write to the /tmp folder
    def copy_json_file(self, file_name, json_obj):
        copied_json_files = []
        new_file_name = ""
        if "templateId" in json_obj and json_obj["templateId"] in [
            "region",
            "agency",
        ]:
            new_file_name = json_obj["name"]
            shutil.copy(file_name, f"/tmp/{new_file_name}.json")
        if "templateId" in json_obj and json_obj["templateId"].lower() in [
            "vehiclev2",
            "phaseselector",
            "communicator",
        ]:
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
        file_path = os.path.join(sys.path[0], f"{file_name}")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                json_str = f.read()
            json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
            json_obj = json.loads(json_str)
            copied_files = self.copy_json_file(file_path, json_obj)
        else:
            print(f"{file_name} not found.")
        return json_obj, copied_files

    def test_check_unique_agency(self):

        # create new region
        region_data, copied_region_files = self.open_json_file("test_region1.json")
        rc_new_region, error_new_region = new_region(region_data["name"])
        assert rc_new_region, error_new_region

        # create agency1 and check uniqueness
        agency_data, copied_agency_files = self.open_json_file("test_agency1.json")
        new_agency(region_data["name"], agency_data["name"])
        rc, error = create_json.check_unique_agency(agency_data)
        assert rc, error

        # create new agency3 and recheck uniqueness
        agency_data3, copied_agency_files3 = self.open_json_file("test_agency3.json")
        new_agency(region_data["name"], agency_data3["name"])
        rc_again, error = create_json.check_unique_agency(agency_data)
        assert not rc_again, error
        assert error == "Error: agencyCode already exists in agency"
        del_agency(region_data["name"], agency_data3["name"])
        del_agency(region_data["name"], agency_data["name"])
        del_region(region_data["name"])
        self.remove_json_file(copied_region_files)
        self.remove_json_file(copied_agency_files)
        self.remove_json_file(copied_agency_files3)

    def test_check_unique_device(self):

        # create new region
        region_data, copied_region_files = self.open_json_file("test_region2.json")
        rc_new_region, error_new_region = new_region(region_data["name"])
        assert rc_new_region, error_new_region

        # create new agency
        agency_data, copied_agency_files = self.open_json_file("test_agency2.json")
        rc_new_agency, error_new_agency = new_agency(
            region_data["name"], agency_data["name"]
        )
        assert rc_new_agency, error_new_agency
        rc, error = create_json.check_unique_agency(agency_data)
        assert rc, error

        # create new communicator and check uniqueness
        communicator_data, copied_communicator_files = self.open_json_file(
            "test_communicator1.json"
        )
        rc, error = new_communicator(
            region_data["name"],
            agency_data["name"],
            None,
            communicator_data["deviceId"],
        )
        assert rc, error
        rc, error = create_json.check_unique_device(communicator_data, ["gttSerial"])
        assert rc, error

        # create new communicator and recheck uniqueness
        communicator_data2, copied_communicator_files2 = self.open_json_file(
            "test_communicator2.json"
        )
        new_communicator(
            region_data["name"],
            agency_data["name"],
            None,
            communicator_data2["deviceId"],
        )
        rc_again, error = create_json.check_unique_device(
            communicator_data2, ["gttSerial"]
        )
        assert not rc_again, error
        assert error == "Error: gttSerial already exists in device"

        # clean up vehicle entity
        del_communicator(
            region_data["name"],
            agency_data["name"],
            None,
            communicator_data["deviceId"],
        )
        del_communicator(
            region_data["name"],
            agency_data["name"],
            None,
            communicator_data2["deviceId"],
        )
        del_agency(region_data["name"], agency_data["name"])
        del_region(region_data["name"])
        self.remove_json_file(copied_region_files)
        self.remove_json_file(copied_agency_files)
        self.remove_json_file(copied_communicator_files)
        self.remove_json_file(copied_communicator_files2)

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
