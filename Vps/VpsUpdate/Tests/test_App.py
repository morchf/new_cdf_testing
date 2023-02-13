import pytest
import os
import json
import sys
from moto import mock_dynamodb2
import boto3

sys.path.append("../")
TXNS_TABLE = "globalMacVps"
TXNS_TABLE2 = "codeBuildDeploy"


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function")
def dynamodb_fixture(aws_credentials):
    mockdynamodb2 = mock_dynamodb2()
    mockdynamodb2.start()
    client = boto3.client("dynamodb", region_name="us-east-1")
    resource = boto3.resource("dynamodb", region_name="us-east-1")

    # create globalMacVps table
    resource.create_table(
        TableName=TXNS_TABLE,
        KeySchema=[{"AttributeName": "primaryKey", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "primaryKey", "AttributeType": "N"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 7},
    )

    # create codeBuildDeploy table
    resource.create_table(
        TableName=TXNS_TABLE2,
        KeySchema=[{"AttributeName": "customerName", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "customerName", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 7},
    )

    table = boto3.resource("dynamodb", region_name="us-east-1").Table(TXNS_TABLE)
    table2 = boto3.resource("dynamodb", region_name="us-east-1").Table(TXNS_TABLE2)
    # insert vps data
    with open("TestVps.json") as json_file:
        data = json.load(json_file)
        for vps in data["globalMacVps"]:
            table.put_item(Item=vps)
        for customer in data["codeBuildDeploy"]:
            table2.put_item(Item=customer)

    yield client, resource

    mockdynamodb2.stop()


# test mock_dynamodb2 is running properly
def test_dynamoDB(dynamodb_fixture):
    table = boto3.resource("dynamodb", region_name="us-east-1").Table(TXNS_TABLE)
    table2 = boto3.resource("dynamodb", region_name="us-east-1").Table(TXNS_TABLE2)
    resp = table.get_item(Key={"primaryKey": 224754296422595})
    assert resp["Item"]["customerName"] == "DALLAS"

    resp2 = table2.get_item(Key={"customerName": "DALLAS"})
    assert resp2["Item"]["ImageId"] == "ami-0878e35d09c75f0a1"


def test_changeStatus(dynamodb_fixture):
    from App import changeStatus

    res = changeStatus("V764DAMS0191", "ACTIVE")
    assert res["body"] == "V764DAMS0191" + " device status successfully updated"
    assert res["statusCode"] == 200

    res = changeStatus("V764DAMS0191", "YES")
    assert res["body"] == "V764DAMS0191" + " device status successfully updated"
    assert res["statusCode"] == 200


def test_changeStatus_failed(dynamodb_fixture):
    from App import changeStatus

    # test with unexisted VPS
    res = changeStatus("V764DAMS9999", "ACTIVE")
    assert res["body"] == "V764DAMS9999" + " name not found"
    assert res["statusCode"] == 404


def test_lambda_handler(dynamodb_fixture):
    from App import lambda_handler

    # test with valid input
    with open("Event.json") as json_file:
        event = json.load(json_file)

    context = "context"
    res = lambda_handler(event, context)
    assert res["body"] == "V764DAMS0191 device status successfully updated"
    assert res["statusCode"] == 200


def test_lambda_handler_incorrect_status(dynamodb_fixture):
    from App import lambda_handler

    # test with incorrect status
    with open("IncorrectStatus.json") as json_file:
        event = json.load(json_file)

    context = "context"
    res = lambda_handler(event, context)
    assert (
        res["body"] == "Invalid VPS device status('ACTIVE':- Keep VPS/Docker in "
        "running state , 'INACTIVE':- Keep VPS/Docker in stop state, 'YES':- "
        "Delete the Docker or 'RESTART':-VPS/Docker to restart)"
    )
    assert res["statusCode"] == 400


def test_lambda_handler_invalid_format(dynamodb_fixture):
    from App import lambda_handler

    # test with invalid format
    with open("InvalidFormat.json") as json_file:
        event = json.load(json_file)

    context = "context"
    res = lambda_handler(event, context)
    assert res["body"] == "Invalid input parameters"
    assert res["statusCode"] == 400
