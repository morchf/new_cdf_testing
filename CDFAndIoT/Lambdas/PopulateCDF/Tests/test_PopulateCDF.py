import pytest
import json
import os
import sys
from unittest.mock import patch

# allow tests to find all the code they need to run
sys.path.append("../lambda-code")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 3 * "/.."), "CDFBackend")
)

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"

import PopulateCDF as populate_cdf  # noqa: E402

ok = "Ok, have a nice day."


# helper functions
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


# tests
def test_check_unique_region():
    with patch("PopulateCDF.list_regions") as mock_region:
        region_list = [
            {
                "attributes": {
                    "caCertId": "NULL_CA",
                    "regionGUID": "NULL_GUID",
                    "regionDNS": "10.20.30.44",
                },
                "category": "group",
                "templateId": "region",
                "parentPath": "/",
                "name": "PortlandMetro",
                "description": "Just deserts",
                "groupPath": "/portlandmetro",
                "relation": "parent",
                "direction": "in",
            }
        ]
        mock_region.return_value = (True, region_list)
        rc, _ = populate_cdf.check_unique_region("PortlandMetro")

    assert rc == True  # noqa: E712


def test_check_unique_region_failed():
    with patch("PopulateCDF.list_regions") as mock_region:
        # 2 regions have same region and regionDNS
        region_list = [
            {
                "attributes": {
                    "caCertId": "NULL_CA",
                    "regionGUID": "NULL_GUID",
                    "regionDNS": "10.20.30.44",
                },
                "category": "group",
                "templateId": "region",
                "parentPath": "/",
                "name": "PortlandMetro2",
                "description": "Just deserts",
                "groupPath": "/portlandmetro",
                "relation": "parent",
                "direction": "in",
            },
            {
                "attributes": {
                    "caCertId": "NULL_CA",
                    "regionGUID": "NULL_GUID",
                    "regionDNS": "10.20.30.44",
                },
                "category": "group",
                "templateId": "region",
                "parentPath": "/",
                "name": "PortlandMetro",
                "description": "Just deserts",
                "groupPath": "/portlandmetro",
                "relation": "parent",
                "direction": "in",
            },
        ]
        mock_region.return_value = (True, region_list)
        rc, error = populate_cdf.check_unique_region("PortlandMetro")
    assert error == "region is not unique"  # noqa: E712
    assert rc == False  # noqa: E712


def test_check_unique_agency():
    region_list = [
        {
            "attributes": {
                "caCertId": "NULL_CA",
                "regionGUID": "NULL_GUID",
                "regionDNS": "10.20.30.44",
            },
            "category": "group",
            "templateId": "region",
            "parentPath": "/",
            "name": "PortlandMetro",
            "description": "Just deserts",
            "groupPath": "/portlandmetro",
            "relation": "parent",
            "direction": "in",
        }
    ]
    agency_list = [
        {
            "attributes": {
                "city": "Oakdale",
                "timezone": "Central",
                "agencyID": "10",
                "agencyCode": 100,
                "priority": "High",
                "vpsCertId": "NULL_CERT",
                "caCertId": "NULL_CA",
                "state": "Mn",
            },
            "category": "group",
            "templateId": "agency",
            "parentPath": "/portlandmetro",
            "name": "FireDept",
            "groupPath": "/portlandmetro/firedept",
            "relation": "parent",
            "direction": "in",
        }
    ]
    with patch("PopulateCDF.list_regions") as mock_region:
        with patch("PopulateCDF.list_agencies") as mock_agency:
            mock_region.return_value = (True, region_list)
            mock_agency.return_value = (True, agency_list)
            rc, _ = populate_cdf.check_unique_agency("FireDept")

    assert rc == True  # noqa: E712


def test_check_unique_agency_failed():
    region_list = [
        {
            "attributes": {
                "caCertId": "NULL_CA",
                "regionGUID": "NULL_GUID",
                "regionDNS": "10.20.30.44",
            },
            "category": "group",
            "templateId": "region",
            "parentPath": "/",
            "name": "PortlandMetro",
            "description": "Just deserts",
            "groupPath": "/portlandmetro",
            "relation": "parent",
            "direction": "in",
        }
    ]
    agency_list = [
        {
            "attributes": {
                "city": "Oakdale",
                "timezone": "Central",
                "agencyID": "10",
                "agencyCode": 100,
                "priority": "High",
                "vpsCertId": "NULL_CERT",
                "caCertId": "NULL_CA",
                "state": "Mn",
            },
            "category": "group",
            "templateId": "agency",
            "parentPath": "/portlandmetro",
            "name": "FireDept",
            "groupPath": "/portlandmetro/firedept",
            "relation": "parent",
            "direction": "in",
        },
        {
            "attributes": {
                "city": "Oakdale",
                "timezone": "Central",
                "agencyID": "10",
                "agencyCode": 100,
                "priority": "High",
                "vpsCertId": "NULL_CERT",
                "caCertId": "NULL_CA",
                "state": "Mn",
            },
            "category": "group",
            "templateId": "agency",
            "parentPath": "/portlandmetro",
            "name": "FireDept2",
            "groupPath": "/portlandmetro/firedept",
            "relation": "parent",
            "direction": "in",
        },
    ]
    with patch("PopulateCDF.list_regions") as mock_region:
        with patch("PopulateCDF.list_agencies") as mock_agency:
            mock_region.return_value = (True, region_list)
            mock_agency.return_value = (True, agency_list)
            rc, error = populate_cdf.check_unique_agency("FireDept")

    assert error == "agency is not unique"  # noqa: E712
    assert rc == False  # noqa: E712


def test_check_unique_device():
    region_list = [
        {
            "attributes": {
                "caCertId": "NULL_CA",
                "regionGUID": "NULL_GUID",
                "regionDNS": "10.20.30.44",
            },
            "category": "group",
            "templateId": "region",
            "parentPath": "/",
            "name": "PortlandMetro",
            "description": "Just deserts",
            "groupPath": "/portlandmetro",
            "relation": "parent",
            "direction": "in",
        }
    ]
    agency_list = [
        {
            "attributes": {
                "city": "Oakdale",
                "timezone": "Central",
                "agencyID": "10",
                "agencyCode": 100,
                "priority": "High",
                "vpsCertId": "NULL_CERT",
                "caCertId": "NULL_CA",
                "state": "Mn",
            },
            "category": "group",
            "templateId": "agency",
            "parentPath": "/portlandmetro",
            "name": "FireDept",
            "groupPath": "/portlandmetro/firedept",
            "relation": "parent",
            "direction": "in",
        }
    ]
    device_list = [
        {
            "attributes": {
                "devCertId": "NULL_CERT",
                "heading": 3,
                "lastGPIOMsgTimestamp": "1576175734002",
                "type": "Ladder Truck",
                "priority": "High",
                "auxiliaryIo": 0,
                "long": -92.9453703,
                "speed": 20,
                "lastGPSMsgTimestamp": "1576175734002",
                "VID": 234,
                "name": "veh1238",
                "fixStatus": 1,
                "numFixSat": 3,
                "class": 9,
                "uniqueId": "NULL_GUID",
                "lat": 44.9512963,
            },
            "category": "device",
            "templateId": "vehiclev2",
            "description": "Tan",
            "deviceId": "firetruck99",
            "state": "active",
            "relation": "ownedby",
            "direction": "in",
        }
    ]
    with patch("PopulateCDF.list_regions") as mock_region:
        with patch("PopulateCDF.list_agencies") as mock_agency:
            with patch("PopulateCDF.list_devices") as mock_device:
                mock_region.return_value = (True, region_list)
                mock_agency.return_value = (True, agency_list)
                mock_device.return_value = (True, device_list)
                rc, _ = populate_cdf.check_unique_device("firetruck99")

    assert rc == True  # noqa: E712


def test_check_unique_device_failed():
    region_list = [
        {
            "attributes": {
                "caCertId": "NULL_CA",
                "regionGUID": "NULL_GUID",
                "regionDNS": "10.20.30.44",
            },
            "category": "group",
            "templateId": "region",
            "parentPath": "/",
            "name": "PortlandMetro",
            "description": "Just deserts",
            "groupPath": "/portlandmetro",
            "relation": "parent",
            "direction": "in",
        }
    ]
    agency_list = [
        {
            "attributes": {
                "city": "Oakdale",
                "timezone": "Central",
                "agencyID": "10",
                "agencyCode": 100,
                "priority": "High",
                "vpsCertId": "NULL_CERT",
                "caCertId": "NULL_CA",
                "state": "Mn",
            },
            "category": "group",
            "templateId": "agency",
            "parentPath": "/portlandmetro",
            "name": "FireDept",
            "groupPath": "/portlandmetro/firedept",
            "relation": "parent",
            "direction": "in",
        }
    ]
    device_list = [
        {
            "attributes": {
                "devCertId": "NULL_CERT",
                "heading": 3,
                "lastGPIOMsgTimestamp": "1576175734002",
                "type": "Ladder Truck",
                "priority": "High",
                "auxiliaryIo": 0,
                "long": -92.9453703,
                "speed": 20,
                "lastGPSMsgTimestamp": "1576175734002",
                "VID": 234,
                "name": "veh1238",
                "fixStatus": 1,
                "numFixSat": 3,
                "class": 9,
                "uniqueId": "NULL_GUID",
                "lat": 44.9512963,
            },
            "category": "device",
            "templateId": "vehiclev2",
            "description": "Tan",
            "deviceId": "firetruck99",
            "state": "active",
            "relation": "ownedby",
            "direction": "in",
        },
        {
            "attributes": {
                "devCertId": "NULL_CERT",
                "heading": 3,
                "lastGPIOMsgTimestamp": "1576175734002",
                "type": "Ladder Truck",
                "priority": "High",
                "auxiliaryIo": 0,
                "long": -92.9453703,
                "speed": 20,
                "lastGPSMsgTimestamp": "1576175734002",
                "VID": 234,
                "name": "veh1238",
                "fixStatus": 1,
                "numFixSat": 3,
                "class": 9,
                "uniqueId": "NULL_GUID",
                "lat": 44.9512963,
            },
            "category": "device",
            "templateId": "vehiclev2",
            "description": "Tan",
            "deviceId": "firetruck88",
            "state": "active",
            "relation": "ownedby",
            "direction": "in",
        },
    ]
    with patch("PopulateCDF.list_regions") as mock_region:
        with patch("PopulateCDF.list_agencies") as mock_agency:
            with patch("PopulateCDF.list_devices") as mock_device:
                mock_region.return_value = (True, region_list)
                mock_agency.return_value = (True, agency_list)
                mock_device.return_value = (True, device_list)
                rc, error = populate_cdf.check_unique_device("firetruck99")
    assert error == "devCertId is NULL_CERT while cert_list is ['NULL_CERT']"
    assert rc == False  # noqa: E712


def test_create_region():
    with patch("PopulateCDF.new_region") as mock_ui:
        with patch("PopulateCDF.check_unique_region") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("event-create-region.json")

            rc, error = populate_cdf.lambda_handler(event, None)

    assert error == ok
    assert rc == True  # noqa: E712


def test_create_region_failed():
    with patch("PopulateCDF.new_region") as mock_ui:
        with patch("PopulateCDF.check_unique_region") as mock_check:
            mock_ui.return_value = (False, "Failed create region")
            mock_check.return_value = (True, ok)
            event = open_json_file("event-create-region.json")

            rc, error = populate_cdf.lambda_handler(event, None)

    assert error == "Failed create region"
    assert rc == False  # noqa: E712


def test_create_agency():
    with patch("PopulateCDF.new_agency") as mock_ui:
        with patch("PopulateCDF.check_unique_agency") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("event-create-agency.json")

            rc, error = populate_cdf.lambda_handler(event, None)

    assert error == ok
    assert rc == True  # noqa: E712


def test_create_agency_failed():
    with patch("PopulateCDF.new_agency") as mock_ui:
        mock_ui.return_value = (False, "Failed create agency")
        event = open_json_file("event-create-agency.json")

        rc, error = populate_cdf.lambda_handler(event, None)

    assert error == "Failed create agency"
    assert rc == False  # noqa: E712


def test_create_vehicle():
    with patch("PopulateCDF.new_vehicle") as mock_ui:
        mock_ui.return_value = (True, ok)
        event = open_json_file("event-create-vehicle.json")

        rc, error = populate_cdf.lambda_handler(event, None)

    assert error == ok
    assert rc == True  # noqa: E712


def test_create_vehicle_failed():
    with patch("PopulateCDF.new_vehicle") as mock_ui:
        mock_ui.return_value = (False, "Failed create device")
        event = open_json_file("event-create-vehicle.json")

        rc, error = populate_cdf.lambda_handler(event, None)

    assert error == "Failed create device"
    assert rc == False  # noqa: E712


def test_create_communicator():
    with patch("PopulateCDF.new_communicator") as mock_ui:
        with patch("PopulateCDF.check_unique_device") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("event-create-comm.json")

            rc, error = populate_cdf.lambda_handler(event, None)

    assert error == ok
    assert rc == True  # noqa: E712


def test_create_communicator_failed():
    with patch("PopulateCDF.new_communicator") as mock_ui:
        mock_ui.return_value = (False, "Failed create device")
        event = open_json_file("event-create-comm.json")

        rc, error = populate_cdf.lambda_handler(event, None)

    assert error == "Failed create device"
    assert rc == False  # noqa: E712


def test_create_ps():
    with patch("PopulateCDF.new_phaseselector") as mock_ui:
        with patch("PopulateCDF.check_unique_device") as mock_check:
            mock_ui.return_value = (True, ok)
            mock_check.return_value = (True, ok)
            event = open_json_file("event-create-ps.json")

            rc, error = populate_cdf.lambda_handler(event, None)

    assert error == ok
    assert rc == True  # noqa: E712


def test_create_ps_failed():
    with patch("PopulateCDF.new_phaseselector") as mock_ui:
        mock_ui.return_value = (False, "Failed create ps")
        event = open_json_file("event-create-ps.json")

        rc, error = populate_cdf.lambda_handler(event, None)

    assert error == "Failed create ps"
    assert rc == False  # noqa: E712


def test_invalid_entity_data():
    with patch("PopulateCDF.check_unique_device") as mock_check:
        mock_check.return_value = (True, ok)
        event = open_json_file("event-invalid.json")

        rc, error = populate_cdf.lambda_handler(event, None)

    assert error == "Invalid input JSON"
    assert rc == False  # noqa: E712


def test_malformed_json_no_taskResult():
    with patch("PopulateCDF.check_unique_device") as mock_check:
        with pytest.raises(Exception) as info:
            mock_check.return_value = (True, ok)
            event = open_json_file("event-malformed-json-no-taskResult.json")

            populate_cdf.lambda_handler(event, None)

    assert str(info.value) == "'taskResult-create-json'"


def test_malformed_json_no_entity_json():
    with patch("PopulateCDF.check_unique_device") as mock_check:
        with pytest.raises(Exception) as info:
            mock_check.return_value = (True, ok)
            event = open_json_file("event-malformed-json-no-entity_json.json")

            populate_cdf.lambda_handler(event, None)

    assert str(info.value) == "'entity_json'"
