import json
import os
import sys
import CDFAndIoT.Lambdas.DeleteFromCache as DeleteFromCache

sys.path.append("../LambdaCode")
sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)

# os.environ["CDF_URL"] = "mock_url"
os.environ["CERT_BKT"] = "bktbkt"
os.environ["AWS_REGION"] = "us-east-1"


def test_receive_message():

    with open("sqs_message.json", "r") as file:
        sqs_from_json = json.load(file)
    message = DeleteFromCache.receive_message()

    assert message["Messages"][0]["Body"] == sqs_from_json["Messages"][0]["Body"]


# trigger a purge from the AWS console before running this failure case
def test_receive_message_failure():

    message = DeleteFromCache.receive_message()

    assert message == {
        "statusCode": 400,
        "body": "Did not receive message from SQS",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }


def test_delete_item_success():
    with open("sqs_message.json", "r") as file:
        sqs_message = json.load(file)

    if sqs_message:
        message = DeleteFromCache.delete_from_cache(sqs_message)

        assert message == {
            "statusCode": 200,
            "body": "Succesfully deleted the updated item from cache",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }


def test_delete_item_failure():
    with open("sqs_message.json", "r") as file:
        sqs_message = json.load(file)
        sqs_message["ResponseMetadata"]["HTTPStatusCode"] = 400

    message = DeleteFromCache.delete_from_cache(sqs_message)

    assert message == {
        "statusCode": 400,
        "body": "Cache item could not be deleted.",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
