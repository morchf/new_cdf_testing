import os
from io import BytesIO
import base64

import boto3

from util.messages import create_messages
from util.csv import parse_form_data, read_csv, read_excel
from util.http import ok, error, not_found
from util.email import Client as EmailClient
from services.queue_job import Client as QueueJob

aws_account = boto3.client("sts").get_caller_identity().get("Account")
aws_region = os.environ["AWS_REGION"]

queue_job = QueueJob(aws_account, aws_region)
email_client = EmailClient(
    os.getenv("SNS_REPORT_TOPIC_ARN"), "Batch CDF Entities Load Results"
)


def parse_event(event):
    params = {}

    # SNS notification
    if (
        "Records" in event
        and len(event["Records"]) != 0
        and "EventSource" in event["Records"][0]
        and event["Records"][0]["EventSource"] == "aws:sns"
    ):
        params = {**event, "type": "finish"}
    # Manual call
    elif "type" in event:
        params = {**event}
    # Query-string params
    elif "queryStringParameters" in event and "type" in event["queryStringParameters"]:
        params = {**event, **event["queryStringParameters"]}
    else:
        raise Exception("Unknown request")

    return params


def complete_job(message_handler_lambda_arn, queue_url=None, topic_arn=None):
    queue_url = queue_url if queue_url else queue_job.from_topic_arn(topic_arn)
    errors = queue_job.errors(QueueUrl=queue_url)

    # Email from queue tag
    tags = queue_job.list_tags(QueueUrl=queue_url)["Tags"]

    # Send message
    if "OwnerEmail" in tags:
        email_client.send_report(tags["OwnerEmail"], errors)

    # Delete queue
    queue_job.delete(
        QueueUrl=queue_url,
        TopicArn=topic_arn,
        MessageHandlerLambdaArn=message_handler_lambda_arn,
    )


def parse_file(body, headers):
    form_data = parse_form_data(base64.b64decode(body), headers)

    if not "file" in form_data or not "type" in form_data:
        raise Exception("Missing form data field")

    # Parse file
    raw_file = form_data["file"][0]
    file_type = form_data["type"][0]

    if file_type == "csv":
        return read_csv(raw_file.decode(), header=True)

    if file_type == "xlsx":
        return read_excel(BytesIO(raw_file))

    raise Exception(f"Unknown file type: {file_type}")


def lambda_handler(event, context):
    """
    Manages a queue job for bulk CDF asset creation. Handles event
    types--create, delete, status, and finish--from three different sources

    - Manually: Designated by the 'type' field
    - API call: Pass in 'type' query-string parameter
    - SNS event: 'finish'

    The 'create' event assumes an 'owner' attribute in the query parameters to
    uniquely identify a job creation source

    Must add the below headers to the 'create' requests
    - Content-Type: multipart/form-data
    - Accept: multipart/form-data

    Must add the file and extension to the 'create' form data
    - file: File data
    - type: Extension
    """

    print(f"lambda_handler(): event = {event}")

    params = parse_event(event)
    print(f"Called type [{params['type']}]")

    attached_lambda_arn = os.getenv("LAMBDA_HANDLER_ARN")
    lambda_arn = context.invoked_function_arn

    if params["type"] == "create":
        assert params["body"]
        assert params["headers"]

        records = None
        messages = None
        try:
            records = parse_file(params["body"], params["headers"])

            # Convert records to SQS messages
            messages = create_messages(records)

            owner = params["owner"]
            email = params.get("email")
        except Exception as e:
            error_message = (
                f"Failed on message create: {messages}"
                if messages
                else f"Failed on template parsing: {records}"
            )
            print(e, error_message)
            return error(f"Issue parsing template. {error_message}")

        # Create queue
        queue_url = None
        try:
            response = queue_job.create(
                Name="CreateCDFEntitiesBatch",
                OwnerId=owner,
                EventHandlerLambdaArn=lambda_arn,
                MessageHandlerLambdaArn=attached_lambda_arn,
                SendErrorsToDeadLetterQueue=False,
                # Attach email to QueueJob run
                Tags={"OwnerEmail": email} if email else {},
            )
            queue_url = response["QueueUrl"]

            # Populate queue
            queue_job.send(QueueUrl=queue_url, Messages=messages)

            # Add user to message group
            if email:
                email_client.subscribe_to_reports(email)
        except Exception as e:
            print(e)
            queue_job.delete(
                QueueUrl=queue_url, MessageHandlerLambdaArn=attached_lambda_arn
            )
            return error("Issue starting job")

        return ok(response, statusCode=202)

    if params["type"] == "status":
        assert params["queue_url"]

        try:
            status = queue_job.status(QueueUrl=params["queue_url"])
        except Exception:
            return not_found()

        if status["Done"]:
            complete_job(
                queue_url=params["queue_url"],
                message_handler_lambda_arn=attached_lambda_arn,
            )

        return ok(status)

    if params["type"] == "finish":
        complete_job(
            topic_arn=params["Records"][0]["Sns"]["TopicArn"],
            message_handler_lambda_arn=attached_lambda_arn,
        )
        return ok()

    if params["type"] == "delete":
        return ok(
            queue_job.delete(
                params["queue_url"], MessageHandlerLambdaArn=attached_lambda_arn
            )
        )

    return error("Unknown request")
