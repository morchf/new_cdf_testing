import json
import CDFAndIoT.Lambdas.GetLiveStatusOfIntersectionsPerAgency as GetLiveStatusOfIntersectionsPerAgency


def test_receive_message_success():
    QueueURL = "https://sqs.us-east-1.amazonaws.com/083011521439/PostLiveStatusOfIntersectionsPerAgency"

    with open("sqs_message_success.json", "r") as file:
        sqs_from_json = json.load(file)
    message = GetLiveStatusOfIntersectionsPerAgency.receive_message(QueueURL)

    assert message["templateId"] == sqs_from_json["templateId"]


# trigger a purge from the AWS console before running this failure case
def test_receive_message_failure():

    QueueURL = "Wrong URL"
    message = GetLiveStatusOfIntersectionsPerAgency.receive_message(QueueURL)

    assert message == Exception("Did not receive message from SQS.")


def test_get_queue_URL_success():
    QueueName = "PostLiveStatusOfIntersectionsPerAgency"

    URL = GetLiveStatusOfIntersectionsPerAgency.get_queue_URL(QueueName)

    assert URL == {
        "https://sqs.us-east-1.amazonaws.com/083011521439/PostLiveStatusOfIntersectionsPerAgency"
    }


def test_get_queue_URL_failure():
    QueueName = "Wrong Name"
    URL = GetLiveStatusOfIntersectionsPerAgency.get_queue_URL(QueueName)

    assert URL == {Exception("Could not get queue URL")}
