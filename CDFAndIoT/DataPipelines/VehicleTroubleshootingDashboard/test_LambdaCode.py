from unittest.mock import patch
import os
import datetime

os.environ["s3Bucket"] = "test"
os.environ["stateMachineArn"] = "test"
os.environ["DashboardName"] = "test"

from LambdaCode import App  # noqa: E402

startedExecution = False


class s3_obj_success(object):
    def read(self):
        tm = datetime.datetime.now() - datetime.timedelta(minutes=15)
        return (
            '{"resultTimestamp": "'
            + tm.strftime("%Y/%m/%d %H:%M:%S")
            + '", "status": "SUCCESS"}'
        )


class s3_obj_old(object):
    def read(self):
        tm = datetime.datetime.now() - datetime.timedelta(minutes=3600)
        return (
            '{"resultTimestamp": "'
            + tm.strftime("%Y/%m/%d %H:%M:%S")
            + '", "status": "SUCCESS"}'
        )


class s3_obj_error(object):
    def read(self):
        raise ConnectionError("Test Exception Raised")


def mock_successful(self, operation_name, kwarg):
    global startedExecution
    if operation_name == "GetObject":
        return {"Body": s3_obj_success()}
    elif operation_name == "ListDashboards":
        return {"DashboardSummaryList": []}
    elif operation_name == "GetCallerIdentity":
        return {}
    elif operation_name == "StartExecution":
        startedExecution = True


def mock_old(self, operation_name, kwarg):
    global startedExecution
    if operation_name == "GetObject":
        return {"Body": s3_obj_old()}
    elif operation_name == "ListDashboards":
        return {"DashboardSummaryList": []}
    elif operation_name == "GetCallerIdentity":
        return {}
    elif operation_name == "StartExecution":
        startedExecution = True


def mock_error(self, operation_name, kwarg):
    global startedExecution
    if operation_name == "GetObject":
        return {"Body": s3_obj_error()}
    elif operation_name == "ListDashboards":
        return {"DashboardSummaryList": []}
    elif operation_name == "GetCallerIdentity":
        return {}
    elif operation_name == "StartExecution":
        startedExecution = True


def test_lambda_handler_15min():
    global startedExecution
    with patch("botocore.client.BaseClient._make_api_call", new=mock_successful):
        App.lambda_handler(None, None)
        assert not startedExecution
        startedExecution = False


def test_lambda_handler_old():
    global startedExecution
    with patch("botocore.client.BaseClient._make_api_call", new=mock_old):
        App.lambda_handler(None, None)
        assert startedExecution
        startedExecution = False


def test_lambda_handler_error():
    global startedExecution
    with patch("botocore.client.BaseClient._make_api_call", new=mock_error):
        App.lambda_handler(None, None)
        assert startedExecution
        startedExecution = False
