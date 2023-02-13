import boto3
import json

sqsClnt = boto3.client("sqs")
qName = "vps.fifo"
qURL = sqsClnt.get_queue_url(QueueName=qName).get("QueueUrl")


def lambda_handler(event, context):
    if event["Records"][0]["eventName"] == "MODIFY":
        x = event["Records"][0]["dynamodb"]["NewImage"]
        print(x)
        sqsClnt.send_message(
            QueueUrl=qURL, MessageBody=json.dumps(x), MessageGroupId="VPS"
        )
