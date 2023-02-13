import pytest
import json
import os
import sys
from unittest.mock import patch
import shutil
import boto3
from moto import mock_ssm

sys.path.append("../lambda-code")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"
os.environ["AWS_REGION"] = "us-east-1"

import CreateJSON as create_json  # noqa: E402

# the json files need to be copied to the /tmp directory, as Lambda is only
# allowed to write to the /tmp folder


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
    if "templateId" in json_obj and json_obj["templateId"].lower() == "vehiclev2":
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


def open_json_file(file_name):
    json_str = None
    json_obj = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
        json_obj = json.loads(json_str)
    else:
        print(f"{file_name} not found.")

    return json_obj


class FakeRequest(object):
    def __init__(self):
        self.headers = ""
        self.body = ""


class FakeResponse(object):
    def __init__(self, object):
        self.status_code = 204
        self.content = object
        self.request = FakeRequest()

    def json(self):
        return self.content


def test_validate_IMEI():
    create_json.validate_IMEI("123456789012345")


def test_validate_IMEI_too_short():
    with pytest.raises(Exception) as info:
        create_json.validate_IMEI("12345")
    assert str(info.value) == "IMEI is not valid"


def test_validate_IMEI_too_long():
    with pytest.raises(Exception) as info:
        create_json.validate_IMEI("12345678901234567890")
    assert str(info.value) == "IMEI is not valid"


def test_validate_IMEI_not_numeric():
    with pytest.raises(Exception) as info:
        create_json.validate_IMEI("12345abcde")
    assert str(info.value) == "IMEI is not valid"


def test_validate_MAC_with_colons():
    create_json.validate_MAC("12:34:56:78:90:12")


def test_validate_MAC_with_dashes():
    create_json.validate_MAC("12-34-56-78-90-12")


def test_validate_MAC_with_no_separator():
    create_json.validate_MAC("123456789012")


def test_validate_MAC_alphanumeric_hex():
    create_json.validate_MAC("AB:CD:EF:68:90:12")


def test_validate_MAC_too_short():
    with pytest.raises(Exception) as info:
        create_json.validate_MAC("12:34:5")
    assert str(info.value) == "MAC address is not valid"


def test_validate_MAC_too_long():
    with pytest.raises(Exception) as info:
        create_json.validate_MAC("12:34:56:78:90:11:00")
    assert str(info.value) == "MAC address is not valid"


def test_validate_MAC_random_space():
    with pytest.raises(Exception) as info:
        create_json.validate_MAC("12: 34:56:78:90:1A")
    assert str(info.value) == "MAC address is not valid"


def test_validate_MAC_outside_hex_range():
    with pytest.raises(Exception) as info:
        create_json.validate_MAC("12:34:56:78:90:1G")
    assert str(info.value) == "MAC address is not valid"


def test_validate_IP_too_short():
    with pytest.raises(Exception) as info:
        create_json.validate_IP("192.168.24")
    assert str(info.value) == "IP address 192.168.24 is not valid"


def test_validate_IP_too_long():
    with pytest.raises(Exception) as info:
        create_json.validate_IP("192.168.24.46.32")
    assert str(info.value) == "IP address 192.168.24.46.32 is not valid"


def test_validate_IP_integer_less_than_0():
    with pytest.raises(Exception) as info:
        create_json.validate_IP("192.168.-1.46")
    assert str(info.value) == "IP address 192.168.-1.46 is not valid"


def test_validate_IP_integer_greater_than_255():
    with pytest.raises(Exception) as info:
        create_json.validate_IP("192.257.24.46")
    assert str(info.value) == "IP address 192.257.24.46 is not valid"


def test_validate_IP_with_characters_as_input():
    with pytest.raises(Exception) as info:
        create_json.validate_IP("ab.ab.ab.ab")
    assert str(info.value) == "IP address ab.ab.ab.ab is not valid"


def test_check_field_length():
    length_dict = {"description": 1000, "name": 200, "city": 200, "state": 20}
    data_dict = {
        "description": "something",
        "name": "cheese",
        "city": "timbuktoo",
        "state": "OK",
    }

    create_json.check_field_length(length_dict, data_dict)


def test_check_field_length_description_too_long():
    length_dict = {"description": 8, "name": 200, "city": 200, "state": 20}
    data_dict = {
        "description": "something",
        "name": "cheese",
        "city": "timbuktoo",
        "state": "OK",
    }
    with pytest.raises(Exception) as info:
        create_json.check_field_length(length_dict, data_dict)
    assert (
        str(info.value)
        == "The field description is 9 characters it must be less than 8 charactor(s)"
    )


def test_check_field_length_state_too_long():
    length_dict = {"description": 1000, "name": 200, "city": 200, "state": 1}
    data_dict = {
        "description": "something",
        "name": "cheese",
        "city": "timbuktoo",
        "state": "OK",
    }
    with pytest.raises(Exception) as info:
        create_json.check_field_length(length_dict, data_dict)
    assert (
        str(info.value)
        == "The field state is 2 characters it must be less than 1 charactor(s)"
    )


def test_create_region():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "region",
        "name",
        "description",
        "displayName",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "region",
        "regtest3",
        "test region",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ]
    rc = create_json.lambda_handler(input["input"], None)

    assert rc["entity_json"] == {
        "attributes": {
            "description": "test region",
            "caCertId": "NULL_CA",
            "regionGUID": "NULL_GUID",
            "displayName": "",
        },
        "category": "group",
        "templateId": "region",
        "parentPath": "/",
        "name": "regtest3",
        "groupPath": "/regtest3",
    }


def test_create_agency():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "agency",
        "name",
        "region",
        "description",
        "city",
        "state",
        "timezone",
        "agencyCode",
        "priority",
        "agencyID",
        "CMSId",
        "displayName",
        "",
        "",
        "",
        "",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "agency",
        "agytest3",
        "regtest3",
        "test agency",
        "Eugene",
        "OR",
        "Pacific",
        "111",
        "High",
        "111",
        "",
        "",
        "",
        "",
        "",
        "",
    ]
    with patch("CreateJSON.check_unique_agency") as uni_grp:
        uni_grp.return_value = (True, "words")
        rc = create_json.lambda_handler(input["input"], None)

    assert rc["entity_json"] == {
        "attributes": {
            "description": "test agency",
            "city": "Eugene",
            "state": "OR",
            "timezone": "Pacific",
            "agencyCode": 111,
            "agencyID": "NULL_GUID",
            "CMSId": "",
            "displayName": "",
            "caCertId": "NULL_CA",
            "vpsCertId": "NULL_CERT",
            "priority": "High",
        },
        "category": "group",
        "templateId": "agency",
        "parentPath": "/regtest3",
        "name": "agytest3",
        "groupPath": "/regtest3/agytest3",
    }


def test_create_agency_uniqueness_fail():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "agency",
        "name",
        "region",
        "description",
        "city",
        "state",
        "timezone",
        "agencyCode",
        "priority",
        "agencyID",
        "CMSId",
        "displayName",
        "",
        "",
        "",
        "",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "agency",
        "agytest3",
        "regtest3",
        "test agency",
        "Eugene",
        "OR",
        "Pacific",
        "111",
        "High",
        "111",
        "",
        "",
        "",
        "",
        "",
        "",
    ]
    with pytest.raises(Exception) as info:
        with patch("CreateJSON.check_unique_agency") as uni_grp:
            uni_grp.side_effect = Exception(
                "Error: agencyCode already exists in agency"
            )
            rc = create_json.lambda_handler(input["input"], None)
            print(rc)

    assert str(info.value) == "Error: agencyCode already exists in agency"


def test_create_vehicleV2():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "vehicleV2",
        "name",
        "region",
        "agency",
        "description",
        "type",
        "priority",
        "class",
        "VID",
        "",
        "",
        "",
        "",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "vehicleV2",
        "unittest veh",
        "unittestreg",
        "unittestagy",
        "test only",
        "",
        "High",
        "10",
        "9629",
        "",
        "",
        "",
        "",
    ]

    with patch("CreateJSON.check_unique_vehicle") as uni_dev:
        uni_dev.return_value = (True, "")
        rc = create_json.lambda_handler(input["input"], None)

    assert rc["entity_json"]["groups"] == {"ownedby": ["/unittestreg/unittestagy"]}
    assert rc["entity_json"]["attributes"] == {
        "name": "unittest veh",
        "description": "test only",
        "type": "",
        "priority": "High",
        "class": 10,
        "VID": 9629,
        "uniqueId": "NULL_GUID",
    }


def test_create_communicator():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "communicator",
        "deviceId",
        "region",
        "agency",
        "description",
        "gttSerial",
        "addressMAC",
        "addressLAN",
        "addressWAN",
        "IMEI",
        "make",
        "model",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "communicator",
        "commtest3",
        "regtest3",
        "agytest3",
        "car MP-70",
        "MP70ts2847",
        "A1:B2:03:04:05:07",
        "10.29.34.89",
        "10.29.35.89",
        "123456789012345",
        "Sierra Wireless",
        "MP-70",
    ]
    with patch("CreateJSON.check_unique_device") as uni_dev:
        with patch("CreateJSON.get_modem_data") as mod:
            uni_dev.return_value = (True, "words")
            mod.return_value = None
            rc = create_json.lambda_handler(input["input"], None)

    assert rc["entity_json"] == {
        "groups": {"ownedby": ["/regtest3/agytest3"]},
        "vehicle": "",
        "attributes": {
            "description": "car MP-70",
            "serial": "commtest3",
            "gttSerial": "MP70ts2847",
            "addressMAC": "A1:B2:03:04:05:07",
            "addressLAN": "10.29.34.89",
            "addressWAN": "10.29.35.89",
            "IMEI": "123456789012345",
            "devCertId": "NULL_CERT",
            "make": "Sierra Wireless",
            "model": "MP-70",
            "uniqueId": "NULL_GUID",
        },
        "category": "device",
        "templateId": "communicator",
        "state": "active",
        "deviceId": "commtest3",
    }


def test_create_communicator_uniqueness_fail():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "communicator",
        "deviceId",
        "region",
        "agency",
        "description",
        "gttSerial",
        "addressMAC",
        "addressLAN",
        "addressWAN",
        "IMEI",
        "make",
        "model",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "communicator",
        "commtest3",
        "regtest3",
        "agytest3",
        "car MP-70",
        "MP70ts2847",
        "A1:B2:03:04:05:07",
        "10.29.34.89",
        "10.29.35.89",
        "123456789012345",
        "Sierra Wireless",
        "MP-70",
    ]
    with pytest.raises(Exception) as info:
        with patch("CreateJSON.check_unique_device") as uni_dev:
            with patch("CreateJSON.get_modem_data") as mod:
                uni_dev.side_effect = Exception("Errors: xxx")
                mod.return_value = None
                rc = create_json.lambda_handler(input["input"], None)
                print(rc)

    assert str(info.value) == "Errors: xxx"


def test_create_phaseselector():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "phaseselector",
        "deviceId",
        "region",
        "agency",
        "description",
        "gttSerial",
        "addressMAC",
        "addressLAN",
        "addressWAN",
        "make",
        "model",
        "",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "phaseselector",
        "7640t32847",
        "regtest3",
        "agytest3",
        "ps MP-70",
        "pstest3",
        "A1:B9:03:04:05:07",
        "10.30.34.89",
        "10.30.35.89",
        "Sierra Wireless",
        "MP-70",
        "",
    ]
    with patch("CreateJSON.check_unique_device") as uni_dev:
        with patch("CreateJSON.get_modem_data") as mod:
            uni_dev.return_value = (True, "words")
            mod.return_value = None
            rc = create_json.lambda_handler(input["input"], None)

    assert rc["entity_json"] == {
        "groups": {"ownedby": ["/regtest3/agytest3"]},
        "attributes": {
            "description": "ps MP-70",
            "gttSerial": "7640t32847",
            "addressMAC": "A1:B9:03:04:05:07",
            "addressLAN": "10.30.34.89",
            "addressWAN": "10.30.35.89",
            "make": "Sierra Wireless",
            "model": "MP-70",
        },
        "category": "device",
        "templateId": "phaseselector",
        "state": "active",
        "deviceId": "7640t32847",
    }


def test_create_phaseselector_uniqueness_fail():
    input = open_json_file("input.json")
    input["input"]["taskResult-consume-csv"]["header"] = [
        "phaseselector",
        "deviceId",
        "region",
        "agency",
        "description",
        "gttSerial",
        "addressMAC",
        "addressLAN",
        "addressWAN",
        "make",
        "model",
    ]
    input["input"]["taskResult-consume-csv"]["row_content"] = [
        "phaseselector",
        "7640t32847",
        "regtest3",
        "agytest3",
        "ps MP-70",
        "pstest3",
        "A1:B9:03:04:05:07",
        "10.30.34.89",
        "10.30.35.89",
        "Sierra Wireless",
        "MP-70",
    ]
    with pytest.raises(Exception) as info:
        with patch("CreateJSON.check_unique_device") as uni_dev:
            with patch("CreateJSON.get_modem_data") as mod:
                uni_dev.side_effect = Exception("Errors: xxx")
                mod.return_value = None
                rc = create_json.lambda_handler(input["input"], None)
                print(rc)

    assert str(info.value) == "Errors: xxx"


def test_get_modem_data():
    # Check for data retrieval with valid SN
    with patch("CreateJSON.requests.get") as mock_url_get:
        with patch("CreateJSON.requests.post") as mock_url_post:
            with mock_ssm():
                client = boto3.client("ssm", os.environ["AWS_REGION"])
                client.put_parameter(
                    Name="SW-API-username", Value="name", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-password", Value="psswrd", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-client-ID", Value="13579", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-client-secret", Value="scrt", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-GTT-Company-Number", Value="2222", Type="String"
                )
                mock_url_get.return_value = FakeResponse({"items": "things"})
                mock_url_post.return_value = FakeResponse({"access_token": "token"})

                serialNumber = "N684570206021035"
                data = create_json.get_modem_data(serialNumber)
    assert data == "things"


def test_get_modem_data_invalid_SN():
    # Check for no data retrieval with invalid SN
    with patch("CreateJSON.requests.get") as mock_url_get:
        with patch("CreateJSON.requests.post") as mock_url_post:
            with mock_ssm():
                client = boto3.client("ssm", os.environ["AWS_REGION"])
                client.put_parameter(
                    Name="SW-API-username", Value="name", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-password", Value="psswrd", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-client-ID", Value="13579", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-client-secret", Value="scrt", Type="String"
                )
                client.put_parameter(
                    Name="SW-API-GTT-Company-Number", Value="2222", Type="String"
                )

                mock_url_post.return_value = FakeResponse({"access_token": "token"})
                mock_url_get.return_value = FakeResponse("")
                serialNumber = "blah"
                data = create_json.get_modem_data(serialNumber)
    assert data == None  # noqa: E711


def test_determine_MP70_data_got_data():
    # Checks if codes succeeds with actual device
    get_data = [
        {
            "gateway": {"macAddress": "03:94:02:8A:02:34", "imei": "358000000000231"},
            "subscription": {"ipAddress": "10.2.3.221"},
        }
    ]

    entity_dict = {
        "addressMAC": "03:94:02:88:02:34",
        "addressWAN": "10.2.3.1",
        "IMEI": "358000000000000",
        "model": "MP-70",
    }

    MP70_data = create_json.determine_MP70_data(entity_dict, get_data)
    assert MP70_data == ["03:94:02:8A:02:34", "10.2.3.221", "358000000000231"]


def test_determine_MP70_data_simulator():
    # Checks if code succeeds when there is a simulated device (no valid serial number)
    get_data = None
    entity_dict = {
        "addressMAC": "03:94:02:88:02:34",
        "addressWAN": "10.2.3.1",
        "IMEI": "358000000000789",
        "model": "MP-70",
    }

    MP70_data = create_json.determine_MP70_data(entity_dict, get_data)
    assert MP70_data == ["03:94:02:88:02:34", "10.2.3.1", "358000000000789"]
