from unittest.mock import patch
import os


os.environ["StackName"] = "Test"
os.environ["DatasetName"] = "test"
os.environ["DashboardName"] = "test"
os.environ["S3DataVizBucket"] = "test"


def mock_api_call(self, operation_name, kwarg):
    print(operation_name)
    if operation_name == "DescribeEndpoint":
        return {"endpointAddress": "test"}
    elif operation_name == "GetParameters":
        return {"Parameters": []}
    elif operation_name == "GetCallerIdentity":
        return {"Account": "test"}
    elif operation_name == "ListDashboards":
        return {"DashboardSummaryList": [{"Name": "test", "DashboardId": "123456"}]}
    elif operation_name == "ListDataSets":
        return {"DataSetSummaries": [{"Name": "test", "DataSetId": "987654"}]}
    elif operation_name == "CreateIngestion":
        return {"IngestionId": 1}
    elif operation_name == "DescribeIngestion":
        return {"Ingestion": {"IngestionStatus": "COMPLETED"}}


def mock_requests_call(method, url):
    print(method)

    class response:
        text = ""

    return response()


with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
    with patch("requests.request", new=mock_requests_call):
        from LambdaCode import App


def mock_send_request(method, url, creds, headers={}, data={}):
    print(method)


def mock_get_device(searchedType, serial):
    return [{"attributes": {}, "deviceId": "123"}]


def mock_listen_to_topic(topic, timeout):
    return []


def test_get_root_ca():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
        with patch("LambdaCode.App.sendRequest", new=mock_send_request):
            assert (
                App.GetAwsRootCa()
                == """-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----
"""
            )


def test_certs_exist_true():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
        with patch("LambdaCode.App.sendRequest", new=mock_send_request):
            if not os.path.exists("/tmp/"):
                os.makedirs("/tmp/")
            for i in ["/tmp/cert.pem", "/tmp/rootca.pem", "/tmp/key.key"]:
                if not os.path.exists(i):
                    open(i, "a").close()
            assert App.CertsExist()


def test_certs_exist_false():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
        with patch("LambdaCode.App.sendRequest", new=mock_send_request):
            for i in ["/tmp/cert.pem", "/tmp/rootca.pem", "/tmp/key.key"]:
                if os.path.exists(i):
                    os.remove(i)
            assert not App.CertsExist()


def test_get_dataset_id():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
        with patch("LambdaCode.App.sendRequest", new=mock_send_request):
            assert App.getDataSetId("test") == "987654"


def test_get_dashboard_id():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
        with patch("LambdaCode.App.sendRequest", new=mock_send_request):
            assert App.getDashboardId("test") == "123456"


def test_lambda_handler():
    with patch("botocore.client.BaseClient._make_api_call", new=mock_api_call):
        with patch("LambdaCode.App.getDevice", new=mock_get_device):
            with patch(
                "LambdaCode.App.ListenToSingleTopicMessage", new=mock_listen_to_topic
            ):
                return_val = App.lambda_handler(
                    {"queryStringParameters": {"serialNumber": "1234"}}, None
                )
                assert (
                    return_val["headers"]["Location"]
                    == "https://us-east-1.quicksight.aws.amazon.com/sn/"
                    "dashboards/123456#p.gttSerialNumber=None&"
                    "p.serialNumber=1234"
                )
