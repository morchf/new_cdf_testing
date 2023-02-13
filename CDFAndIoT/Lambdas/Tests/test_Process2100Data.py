import pytest
import json
import os
import sys
from unittest.mock import Mock, patch

# allow tests to find all the code they needs to run
sys.path.append("../Process2100Data/lambda-code")

os.environ["AWS_REGION"] = "us-east-1"
os.environ["CDF_URL"] = "mock_url"

import Process2100Data as data2100


def test_valid_data(mock_event):
    resp = data2100.lambda_handler(mock_event, None)
    assert resp.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_no_topic(mock_event):
    with pytest.raises(Exception) as info:
        del mock_event["topic"]
        resp = data2100.lambda_handler(mock_event, None)
    assert str(info.value) == "No topic in event data"


def test_incompatible_topic(mock_event):
    with pytest.raises(Exception) as info:
        mock_event["topic"] = mock_event.get("topic").replace("GTT", "somerandom")
        resp = data2100.lambda_handler(mock_event, None)
    assert str(info.value) == "incompatible topic name"
