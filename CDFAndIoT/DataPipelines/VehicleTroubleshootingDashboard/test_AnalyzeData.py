# flake8: noqa
# pylint: disable=unused-variable,unsubscriptable-object
from unittest.mock import patch
import datetime
import json
import sys

sys.modules["awsglue.utils"] = __import__("test_fake_getResolvedOptions")

putObjectBody = None
putObjectResults = None


def mock_api_call_no_data(self, operation_name, kwarg):
    global putObjectBody
    global putObjectResults
    print(operation_name)
    if operation_name == "PutObject":
        if putObjectBody is None:
            putObjectBody = kwarg["Body"]
        elif putObjectResults is None:
            putObjectsResults = kwarg["Body"]


def test_analyze_data_no_data():
    global putObjectBody
    global putObjectResults
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call_no_data):
        from AnalyzeDataFunction import App

        putObjectBody = json.loads(putObjectBody)
        assert putObjectBody["status"] == "SUCCESS"
        assert (
            datetime.datetime.strptime(
                putObjectBody["resultTimestamp"], "%Y/%m/%d %H:%M:%S"
            )
            <= datetime.datetime.now()
        )

        assert putObjectResults is None

        putObjectBody = None
        putObjectResults = None
