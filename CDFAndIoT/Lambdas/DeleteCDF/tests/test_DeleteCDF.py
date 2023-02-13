import pytest
import os
import sys
from unittest.mock import patch, call

# allow tests to find all the code they needs to run
sys.path.append("../lambda-code")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"

import DeleteCDF as d  # noqa: E402


def open_json_file(file_name):
    json_str = None
    if os.path.exists(file_name):
        with open(f"{file_name}", "r") as f:
            json_str = f.read()
        json_str = json_str.replace("\r", "").replace("\n", "").replace(" ", "")
    else:
        print(f"{file_name} not found.")
    return json_str


def test_no_taskResult():
    with pytest.raises(Exception) as info:
        event = {}

        rc = d.lambda_handler(event, None)
        print(rc)
    assert str(info.value) == "No entities to delete"


def test_one_delete_region():
    with patch("DeleteCDF.del_region") as mock_del_reg:
        with patch("DeleteCDF.list_agencies") as mock_list_agy:
            mock_list_agy.return_value = (True, [])
            mock_del_reg.return_value = (
                True,
                "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST",
            )
            event = {
                "taskResult-consume-csv": {
                    "regions": "r1",
                    "agencies": "",
                    "vehicles": "",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)
    assert rc == (True, "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST")
    mock_list_agy.assert_called_once_with("r1")
    mock_del_reg.assert_called_once_with("r1")


def test_two_delete_regions():
    with patch("DeleteCDF.del_region") as mock_del_reg:
        with patch("DeleteCDF.list_agencies") as mock_list_agy:
            mock_list_agy.return_value = (True, [])
            mock_del_reg.return_value = (
                True,
                "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST",
            )
            event = {
                "taskResult-consume-csv": {
                    "regions": "r1,r2",
                    "agencies": "",
                    "vehicles": "",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)
    assert rc == (True, "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST")
    assert mock_list_agy.call_count == 2
    assert mock_del_reg.call_count == 2


def test_two_delete_regions_with_children():
    with patch("DeleteCDF.del_region") as mock_del_reg:
        with patch("DeleteCDF.list_agencies") as mock_list_agy:
            mock_list_agy.side_effect = [(True, ["a1"]), (True, ["a2"])]
            mock_del_reg.return_value = (
                True,
                "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST",
            )
            event = {
                "taskResult-consume-csv": {
                    "regions": "r1,r2",
                    "agencies": "",
                    "vehicles": "",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)
    assert rc == False  # noqa: E712
    assert mock_list_agy.call_count == 2
    mock_del_reg.assert_not_called()


def test_one_delete_agency():
    with patch("DeleteCDF.del_agency") as mock_del_agy:
        with patch("DeleteCDF.list_devices") as mock_list_dev:
            mock_list_dev.return_value = (True, [])
            mock_del_agy.return_value = (
                True,
                "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST",
            )
            event = {
                "taskResult-consume-csv": {
                    "regions": "",
                    "agencies": "r1/a1",
                    "vehicles": "",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)
    assert rc == (True, "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST")
    mock_list_dev.assert_called_once_with("r1", "a1")
    mock_del_agy.assert_called_once_with("r1", "a1")


def test_two_delete_agencies():
    with patch("DeleteCDF.del_agency") as mock_del_agy:
        with patch("DeleteCDF.list_devices") as mock_list_dev:
            mock_list_dev.return_value = (True, [])
            mock_del_agy.return_value = (
                True,
                "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST",
            )
            event = {
                "taskResult-consume-csv": {
                    "regions": "",
                    "agencies": "r1/a1,r1/a2",
                    "vehicles": "",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)
    assert rc == (True, "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST")
    assert mock_del_agy.call_count == 2
    assert mock_list_dev.call_count == 2


def test_two_delete_agencies_with_children():
    with patch("DeleteCDF.del_region") as mock_del_agy:
        with patch("DeleteCDF.list_devices") as mock_list_dev:
            mock_list_dev.side_effect = [(True, ["v1"]), (True, ["v2"])]
            mock_del_agy.return_value = (
                True,
                "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST",
            )
            event = {
                "taskResult-consume-csv": {
                    "regions": "",
                    "agencies": "r1/a1,r1/a2",
                    "vehicles": "",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)
    assert rc == False  # noqa: E712
    assert mock_list_dev.call_count == 2
    mock_del_agy.assert_not_called()


def test_delete_one_vehicle():
    with patch("DeleteCDF.del_vehicle") as mock_del_veh:
        with patch("DeleteCDF.list_vehicles") as mock_list_veh:
            mock_list_veh.side_effect = [
                (
                    True,
                    [
                        {
                            "attributes": {
                                "VID": 1,
                                "name": "v1",
                                "priority": "High",
                                "type": "ambulance",
                                "class": 1,
                                "uniqueId": "1EEFF854-C880-11EB-A3B6-9AE58D746495",
                            },
                            "category": "device",
                            "templateId": "vehiclev2",
                            "description": "demo vehicle",
                            "state": "active",
                            "deviceId": "1eeff854-c880-11eb-a3b6-9ae58d746495",
                            "relation": "ownedby",
                            "direction": "in",
                        }
                    ],
                )
            ]
            mock_del_veh.return_value = True
            event = {
                "taskResult-consume-csv": {
                    "regions": "",
                    "agencies": "",
                    "vehicles": "r1/a1/v1",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)  # noqa: E712
    assert rc == True  # noqa: E712
    mock_del_veh.assert_called_once_with(
        "r1", "a1", "1eeff854-c880-11eb-a3b6-9ae58d746495"
    )


def test_delete_two_vehicles():
    with patch("DeleteCDF.del_vehicle") as mock_del_veh:
        with patch("DeleteCDF.list_vehicles") as mock_list_veh:
            mock_list_veh.side_effect = [
                (
                    True,
                    [
                        {
                            "attributes": {
                                "VID": 1,
                                "name": "v1",
                                "priority": "High",
                                "type": "ambulance",
                                "class": 1,
                                "uniqueId": "",
                            },
                            "category": "device",
                            "templateId": "vehiclev2",
                            "description": "demo vehicle",
                            "state": "active",
                            "deviceId": "1eeff854-c880-11eb-a3b6-9ae58d746495",
                            "relation": "ownedby",
                            "direction": "in",
                        },
                        {
                            "attributes": {
                                "VID": 1,
                                "name": "v2",
                                "priority": "High",
                                "type": "ambulance",
                                "class": 1,
                                "uniqueId": "",
                            },
                            "category": "device",
                            "templateId": "vehiclev2",
                            "description": "demo vehicle",
                            "state": "active",
                            "deviceId": "a12332854-c880-11eb-a3b6-9ae58d7463q",
                            "relation": "ownedby",
                            "direction": "in",
                        },
                    ],
                )
            ]
            mock_del_veh.return_value = True
            event = {
                "taskResult-consume-csv": {
                    "regions": "",
                    "agencies": "",
                    "vehicles": "r1/a1/v1,r1/a1/v2",
                    "phase_selectors": "",
                    "communicators": "",
                    "invalid_rows": "0",
                }
            }

            rc = d.lambda_handler(event, None)  # noqa: E712
    assert rc == True  # noqa: E712
    mock_del_veh.assert_has_calls(
        [
            call("r1", "a1", "1eeff854-c880-11eb-a3b6-9ae58d746495"),
            call("r1", "a1", "a12332854-c880-11eb-a3b6-9ae58d7463q"),
        ],
        any_order=True,
    )


def test_delete_one_communicator():
    with patch("DeleteCDF.del_communicator") as mock_del_comm:
        mock_del_comm.return_value = True
        event = {
            "taskResult-consume-csv": {
                "regions": "",
                "agencies": "",
                "vehicles": "",
                "phase_selectors": "",
                "communicators": "r1/a1/c1",
                "invalid_rows": "0",
            }
        }

        rc = d.lambda_handler(event, None)  # noqa: E712
    assert rc == True  # noqa: E712
    mock_del_comm.called_once_with("r1", "a1", "c1")


def test_delete_two_communicators():
    with patch("DeleteCDF.del_communicator") as mock_del_comm:
        mock_del_comm.return_value = True
        event = {
            "taskResult-consume-csv": {
                "regions": "",
                "agencies": "",
                "vehicles": "",
                "phase_selectors": "",
                "communicators": "r1/a1/c1,r1/a1/c2",
                "invalid_rows": "0",
            }
        }

        rc = d.lambda_handler(event, None)
    assert rc == True  # noqa: E712
    mock_del_comm.called_with("r1", "a1", "c1")
    mock_del_comm.called_with("r1", "a1", "c2")


def test_delete_one_phaseselector():
    with patch("DeleteCDF.del_phaseselector") as mock_del_ps:
        mock_del_ps.return_value = True
        event = {
            "taskResult-consume-csv": {
                "regions": "",
                "agencies": "",
                "vehicles": "",
                "phase_selectors": "r1/a1/ps1",
                "communicators": "",
                "invalid_rows": "0",
            }
        }

        rc = d.lambda_handler(event, None)  # noqa: E712
    assert rc == True  # noqa: E712
    mock_del_ps.called_once_with("r1", "a1", "ps1")


def test_delete_two_phaseselectors():
    with patch("DeleteCDF.del_phaseselector") as mock_del_ps:
        mock_del_ps.return_value = True
        event = {
            "taskResult-consume-csv": {
                "regions": "",
                "agencies": "",
                "vehicles": "",
                "phase_selectors": "r1/a1/ps1,r1/a1/ps2",
                "communicators": "",
                "invalid_rows": "0",
            }
        }

        rc = d.lambda_handler(event, None)  # noqa: E712
    assert rc == True  # noqa: E712
    mock_del_ps.called_with("r1", "a1", "ps1")
    mock_del_ps.called_with("r1", "a1", "ps2")
