import json
import os
from unittest.mock import patch
import asset_lib


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
    else:
        print(f"{file_name} not found.")
    json_obj = json.loads(json_str)
    return json_obj


class FakeRequest(object):
    def __init__(self):
        self.headers = ""
        self.body = ""


class FakeResponse(object):
    def __init__(self):
        self.status_code = 204
        self.content = ""
        self.request = FakeRequest()


def test_create_region():
    with patch("asset_lib.requests.post") as mock_create_region_request:
        request = {"headers": "", "body": ""}
        mock_create_region_request.return_value = FakeResponse()
        event = open_json_file("test-files/r1.json")
        rc, content = asset_lib.region_create(event["name"], str(event))

    assert content == ""
    assert rc == 204


def test_create_agency():
    with patch("asset_lib.requests.post") as mock_create_agency_request:
        mock_create_agency_request.return_value = FakeResponse()
        event = open_json_file("test-files/a1.json")
        rc, content = asset_lib.agency_create(event["name"], str(event))

    assert content == ""
    assert rc == 204


def test_create_device():
    with patch("asset_lib.requests.post") as mock_create_device_request:
        mock_create_device_request.return_value = FakeResponse()
        event = open_json_file("test-files/v1.json")
        rc, content = asset_lib.device_create(json.dumps(event))

    assert content == ""
    assert rc == 204


def test_write_region():
    with patch("asset_lib.requests.patch") as mock_write_region_request:
        mock_write_region_request.return_value = FakeResponse()
        event = open_json_file("test-files/r1.json")
        rc, content = asset_lib.region_write(event["name"], json.dumps(event))
    assert content == ""
    assert rc == 204


def test_write_agency():
    with patch("asset_lib.requests.patch") as mock_write_agency_request:
        mock_write_agency_request.return_value = FakeResponse()
        region_json = open_json_file("test-files/r1.json")
        agency_json = open_json_file("test-files/a1.json")
        rc, content = asset_lib.agency_write(
            region_json["name"], agency_json["name"], json.dumps(agency_json)
        )
    assert content == ""
    assert rc == 204


def test_write_device():
    with patch("asset_lib.requests.patch") as mock_write_device_request:
        mock_write_device_request.return_value = FakeResponse()
        device_json = open_json_file("test-files/v1.json")
        rc, content = asset_lib.device_write(
            device_json["deviceId"], json.dumps(device_json)
        )
    assert content == ""
    assert rc == 204


def test_read_region():
    with patch("asset_lib.requests.get") as mock_read_region_request:
        mock_read_region_request.return_value = FakeResponse()
        region_json = open_json_file("test-files/r1.json")
        rc, content = asset_lib.region_read(region_json["name"])
    assert content == ""
    assert rc == 204


def test_read_agency():
    with patch("asset_lib.requests.get") as mock_read_agency_request:
        mock_read_agency_request.return_value = FakeResponse()
        region_json = open_json_file("test-files/r1.json")
        agency_json = open_json_file("test-files/a1.json")
        rc, content = asset_lib.agency_read(region_json["name"], agency_json["name"])
    assert content == ""
    assert rc == 204


def test_read_device():
    with patch("asset_lib.requests.get") as mock_read_device_request:
        mock_read_device_request.return_value = FakeResponse()
        device_json = open_json_file("test-files/v1.json")
        rc, content = asset_lib.device_read(device_json["deviceId"])
    assert content == ""
    assert rc == 204


def test_delete_region():
    with patch("asset_lib.requests.delete") as mock_delete_region_request:
        mock_delete_region_request.return_value = FakeResponse()
        region_json = open_json_file("test-files/r1.json")
        rc, content = asset_lib.region_delete(region_json["name"])
    assert content == ""
    assert rc == 204


def test_delete_agency():
    with patch("asset_lib.requests.delete") as mock_delete_agency_request:
        mock_delete_agency_request.return_value = FakeResponse()
        region_json = open_json_file("test-files/r1.json")
        agency_json = open_json_file("test-files/a1.json")
        rc, content = asset_lib.agency_delete(region_json["name"], agency_json["name"])
    assert content == ""
    assert rc == 204


def test_delete_device():
    with patch("asset_lib.requests.delete") as mock_delete_device_request:
        mock_delete_device_request.return_value = FakeResponse()
        device_json = open_json_file("test-files/v1.json")
        rc, content = asset_lib.device_delete(device_json["deviceId"])
    assert content == ""
    assert rc == 204


def test_list_all_agencies_in_region():
    with patch("asset_lib.requests.get") as mock_get_agencies_in_region_request:
        mock_get_agencies_in_region_request.return_value = FakeResponse()
        region_json = open_json_file("test-files/r1.json")
        rc, content = asset_lib.list_all_agencies_in_region(region_json["name"])
    assert content == ""
    assert rc == 204


def test_list_all_regions():
    with patch("asset_lib.requests.get") as mock_list_regions_request:
        mock_list_regions_request.return_value = FakeResponse()
        rc, content = asset_lib.list_all_regions()
    assert content == ""
    assert rc == 204
