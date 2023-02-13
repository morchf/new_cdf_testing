import os
import sys
import json
from unittest.mock import patch

# allow tests to find all the code they needs to run
sys.path.append("../LambdaCode")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "http://mock_url"
os.environ["CERT_BKT"] = "bktbkt"

import DeleteCDFEntitiesAPI  # noqa: E402


def test_no_taskResult():
    event = {"body": "{}"}
    message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Error: No entities to delete"


def test_one_delete_region():
    with patch("DeleteCDFEntitiesAPI.del_region") as mock_del_reg:
        with patch("DeleteCDFEntitiesAPI.list_agencies") as mock_list_agy:
            mock_list_agy.return_value = (True, [])
            mock_del_reg.return_value = (
                True,
                "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST",
            )
            event = {"body": '{"regions": ["r1"]}'}

            message = DeleteCDFEntitiesAPI.lambda_handler(event, None)
    assert message["body"] == "Successfully deleted"
    mock_list_agy.assert_called_once_with("r1")
    mock_del_reg.assert_called_once_with("r1")


def test_two_delete_region():
    with patch("DeleteCDFEntitiesAPI.del_region") as mock_del_reg:
        with patch("DeleteCDFEntitiesAPI.list_agencies") as mock_list_agy:
            mock_list_agy.return_value = (True, [])
            mock_del_reg.return_value = (
                True,
                "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST",
            )
            event = {"body": '{"regions": ["r1","r2"]}'}

            message = DeleteCDFEntitiesAPI.lambda_handler(event, None)
    assert message["body"] == "Successfully deleted"
    assert mock_list_agy.call_count == 2
    assert mock_del_reg.call_count == 2


def test_two_delete_regions_with_children():
    with patch("DeleteCDFEntitiesAPI.del_region") as mock_del_reg:
        with patch("DeleteCDFEntitiesAPI.list_agencies") as mock_list_agy:
            mock_list_agy.side_effect = [(True, ["a1"]), (True, ["a2"])]
            mock_del_reg.return_value = (
                True,
                "Region Delete Status = REGION_STATUS_DOES_NOT_EXIST",
            )
            event = {"body": '{"regions": ["r1","r2"]}'}

            message = DeleteCDFEntitiesAPI.lambda_handler(event, None)
    assert message["body"] == (
        "Region r1: Region has children, cannot be deleted until children are removed\n"
        + "Region r2: Region has children, cannot be deleted until children are removed"
    )
    assert mock_list_agy.call_count == 2
    assert mock_del_reg.call_count == 0


def test_one_delete_agency():
    with patch("DeleteCDFEntitiesAPI.del_agency") as mock_del_agy:
        with patch("DeleteCDFEntitiesAPI.list_devices") as mock_list_dev:
            mock_list_dev.return_value = (True, [])
            mock_del_agy.return_value = (
                True,
                "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST",
            )
            event = {"body": '{"agencies": ["r1/a1"]}'}

            message = DeleteCDFEntitiesAPI.lambda_handler(event, None)
    assert message["body"] == "Successfully deleted"
    mock_list_dev.assert_called_once_with("r1", "a1")
    mock_del_agy.assert_called_once_with("r1", "a1")


def test_two_delete_agencies():
    with patch("DeleteCDFEntitiesAPI.del_agency") as mock_del_agy:
        with patch("DeleteCDFEntitiesAPI.list_devices") as mock_list_dev:
            mock_list_dev.return_value = (True, [])
            mock_del_agy.return_value = (
                True,
                "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST",
            )
            event = {"body": '{"agencies": ["r1/a1","r1/a2"]}'}

            message = DeleteCDFEntitiesAPI.lambda_handler(event, None)
    assert message["body"] == "Successfully deleted"
    assert mock_del_agy.call_count == 2
    assert mock_list_dev.call_count == 2


def test_two_delete_agencies_with_children():
    with patch("DeleteCDFEntitiesAPI.del_agency") as mock_del_agy:
        with patch("DeleteCDFEntitiesAPI.list_devices") as mock_list_dev:
            mock_list_dev.side_effect = [(True, ["v1"]), (True, ["v2"])]
            mock_del_agy.return_value = (
                True,
                "Agency Delete Status = AGENCY_STATUS_DOES_NOT_EXIST",
            )
            event = {"body": '{"agencies": ["r1/a1","r1/a2"]}'}
            message = DeleteCDFEntitiesAPI.lambda_handler(event, None)
    assert message["body"] == (
        "Agency a1: Agency has children, cannot be deleted until children are removed\n"
        + "Agency a2: Agency has children, cannot be deleted until children are removed"
    )
    assert mock_list_dev.call_count == 2
    mock_del_agy.assert_not_called()


def test_delete_one_vehicle():
    with patch("DeleteCDFEntitiesAPI.del_vehicle") as mock_del_veh:
        mock_del_veh.return_value = (
            True,
            "Device Delete Status = DEVICE_STATUS_DOES_NOT_EXIST",
        )
        event = {"body": '{"vehicles": ["r1/a1/v1"]}'}
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Successfully deleted"
    mock_del_veh.called_once_with("r1", "a1", "v1")


def test_delete_two_vehicles():
    with patch("DeleteCDFEntitiesAPI.del_vehicle") as mock_del_veh:
        mock_del_veh.return_value = (
            True,
            "Device Delete Status = DEVICE_STATUS_DOES_NOT_EXIST",
        )
        event = {"body": '{"vehicles": ["r1/a1/v1","r1/a1/v2"]}'}
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Successfully deleted"
    mock_del_veh.called_with("r1", "a1", "v1")
    mock_del_veh.called_with("r1", "a1", "v2")


def test_delete_one_communicator():
    with patch("DeleteCDFEntitiesAPI.del_communicator") as mock_del_comm:
        mock_del_comm.return_value = (
            True,
            "Device Delete Status = DEVICE_STATUS_DOES_NOT_EXIST",
        )
        event = {"body": '{"communicators": ["r1/a1/c1"]}'}
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Successfully deleted"
    mock_del_comm.called_once_with("r1", "a1", "c1")


def test_delete_two_communicators():
    with patch("DeleteCDFEntitiesAPI.del_communicator") as mock_del_comm:
        mock_del_comm.return_value = (
            True,
            "Device Delete Status = DEVICE_STATUS_DOES_NOT_EXIST",
        )
        event = {"body": '{"communicators": ["r1/a1/c1","r1/a1/c2"]}'}
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Successfully deleted"
    mock_del_comm.called_with("r1", "a1", "c1")
    mock_del_comm.called_with("r1", "a1", "c2")


def test_delete_one_phaseselector():
    with patch("DeleteCDFEntitiesAPI.del_phaseselector") as mock_del_ps:
        mock_del_ps.return_value = (
            True,
            "Device Delete Status = DEVICE_STATUS_DOES_NOT_EXIST",
        )
        event = {"body": '{"phase_selectors": ["r1/a1/ps1"]}'}
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Successfully deleted"
    mock_del_ps.called_once_with("r1", "a1", "ps1")


def test_delete_two_phaseselectors():
    with patch("DeleteCDFEntitiesAPI.del_phaseselector") as mock_del_ps:
        mock_del_ps.return_value = (
            True,
            "Device Delete Status = DEVICE_STATUS_DOES_NOT_EXIST",
        )
        event = {"body": '{"phase_selectors": ["r1/a1/ps1","r1/a1/ps2"]}'}
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message["body"] == "Successfully deleted"
    mock_del_ps.called_with("r1", "a1", "ps1")
    mock_del_ps.called_with("r1", "a1", "ps2")


def mocked_requests_delete(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse(None, 200)


def test_dissociate_vehicle_communicator():
    with patch("requests.delete", side_effect=mocked_requests_delete):
        event = {
            "body": {
                "vehicleName": "zoeVeh",
                "selected": ["zoeCommu"],
                "relationship": "True",
            }
        }
        event["body"] = json.dumps(event["body"])
        message = DeleteCDFEntitiesAPI.lambda_handler(event, None)

    assert message == {
        "statusCode": 200,
        "body": "Successfully dissociate zoeCommu with zoeVeh",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
