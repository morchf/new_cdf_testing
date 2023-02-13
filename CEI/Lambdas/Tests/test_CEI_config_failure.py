# flake8: noqa
# fmt: off
import json
import uuid
import pytest
import requests.auth
from CEI_TestSetup import *

def test_incident_key_failure():
    """Test to ensure a faulty (Broken Key) call is handled properly
    API must return 400 error or the test fails
    """

    data = open_json_file("KeyErrorTest.json", False)
    data_call = json.dumps(data).replace("RANDOMIZEGUID", str(uuid.uuid4()))
    api_url = get_API_url()
    # Get API Token
    headers["Authorization"] = get_API_token()

    # construct API Call
    incident_url = f"{api_url}/cad/incidents"
    incident_post_results = requests.post(incident_url, data=data_call, headers=headers)
    if "400" not in str(incident_post_results):
        pytest.fail(f"API post has failed - response: {str(incident_post_results)}")


def test_config_msg_bad_format():
    """Test that the configuration call handles msg format failures gracefully
    Fails if the resulting response indicates success
    """
    data = open_json_file("ConfigurationBadFormatCall.json", False)
    data_call = json.dumps(data).replace("'", '"').replace("|||", "'").replace("|", "")
    api_url = get_API_url()
    # construct API Call
    config_url = f"{api_url}/cad/configuration"
    config_post_results = requests.post(config_url, data=data_call, headers=headers)
    if "200" in str(config_post_results):
        pytest.fail(f"API post has failed - response: {str(config_post_results)}")


def test_config_msg_incomplete():
    """Test that the configuration call handles incomplete failures gracefully
    Fails if the resulting response indicates success
    """
    data = open_json_file("ConfigurationIncompleteCall.json", False)
    data_call = json.dumps(data).replace("'", '"').replace("|||", "'").replace("|", "")
    api_url = get_API_url()
    # construct API Call
    config_url = f"{api_url}/cad/configuration"
    config_post_results = requests.post(config_url, data=data_call, headers=headers)
    if "200" in str(config_post_results):
        pytest.fail(f"API post has failed - response: {str(config_post_results)}")

# fmt: on
