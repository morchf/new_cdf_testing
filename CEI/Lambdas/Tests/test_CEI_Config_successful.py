# flake8: noqa
# fmt: off
import json
import requests.auth
import pytest
from CEI_TestSetup import *

@pytest.fixture(scope='module')
def setup():
    clear_test_data()
    global site_id 
    site_id = create_region('CEIRegion.json').get('name')
    time.sleep(1)
    global agency_id 
    agency_id = create_agency('CEIAgencyTwo.json').get('name')
    time.sleep(1)



def test_configuration_assignment(setup):
    """Basic configuration assignment test -
    fails if the CDF cannot be reached/does not respond with 200
    fails if any of the fields within configuration_success_call.json do NOT successfully get assigned in the CDF

    """
    data = open_json_file("ConfigurationSuccessCall.json", False)
    data_call = json.dumps(data).replace("'", '"').replace("|||", "'").replace("|", "")
    api_url = get_API_url()
    # construct API Call
    config_url = f"{api_url}/cad/configuration"
    headers["Authorization"] = get_API_token()
    config_post_results = requests.post(config_url, data=data_call, headers=headers)
    if "200" not in str(config_post_results):
        print(api_url)
        pytest.fail(f"API post has failed - response: {str(config_post_results.__dict__)}")

    url_action = f"/groups/%2F{site_id}%2F{agency_id}"
    url_complete = f"{CDF_URL}/{url_action}"

    agency = json.loads(
        send_request(
            url_complete,
            "GET",
            AWS_REGION,
            headers=headers,
        ).content
    )["attributes"]
    failures = []

    # check each field value against the CDF
    if str(agency["CEIUnitIDConfig"]) != str(data["unitIDConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIUnitIDConfig- {agency['CEIUnitIDConfig']} \r\n File Value - {data['unitIDConfig']}"
        )

    if str(agency["CEIUnitTypeConfig"]) != str(data["unitTypeConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIUnitTypeConfig - {agency['CEIUnitTypeConfig']} \r\n File Value - {data['unitTypeConfig']}"
        )

    if str(agency["CEIIncidentTypeConfig"]) != str(data["incidentTypeConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentTypeConfig - {agency['CEIIncidentTypeConfig']} \r\n File Value - {data['incidentTypeConfig']}"
        )

    if str(agency["CEIIncidentTypeConfig"]) != str(data["incidentTypeConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentTypeConfig - {agency['CEIIncidentTypeConfig']} \r\n File Value - {data['incidentTypeConfig']}"
        )

    if str(agency["CEIIncidentStatusConfig"]) != str(data["incidentStatusConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentStatusConfig - {agency['CEIIncidentStatusConfig']} \r\n File Value - {data['incidentStatusConfig']}"
        )

    if str(agency["CEIIncidentPriorityConfig"]) != str(data["incidentPriorityConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIIncidentPriorityConfig - {agency['CEIIncidentPriorityConfig']} \r\n File Value - {data['incidentPriorityConfig']}"
        )

    if str(agency["CEIUnitStatusConfig"]) != str(data["unitStatusConfig"]):
        failures.append(
            f"Update Failure: \n\r CEIUnitStatusConfig - {agency['CEIUnitStatusConfig']} \r\n File Value - {data['unitStatusConfig']}"
        )

    if len(failures) > 0:
        print(*failures, sep="\n")
        pytest.fail(str(failures), True)

# fmt: on
