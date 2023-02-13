from time import time, sleep
import json

import boto3

# Resources
sqs = boto3.resource("sqs")

# Clients
sqs_client = boto3.client("sqs")
sns_client = boto3.client("sns")
cw_client = boto3.client("cloudwatch")
lambda_client = boto3.client("lambda")

"""
Utility
"""


def chunk(arr, n):
    """
    Group array into chunks

    Args:
        l: Array
        n: Max size of each chunk

    Returns: Iterator with each batch
    """
    for i in range(0, len(arr), n):
        yield arr[i : (i + n)]  # noqa: E203


class Client:
    """
    Client representing a job run using an SQS queue as a backing system
    """

    DEFAULT_BATCH_SIZE = 10

    def __init__(self, account, region, batch_size=DEFAULT_BATCH_SIZE):
        self._account = account
        self._region = region

        self._batch_size = batch_size

    """
    ID
    """

    def _topic_id(self, id):
        return f"{id}-sns"

    def _queue_id(self, id, error=False):
        if error:
            return f"{id}-error.fifo"

        return f"{id}.fifo"

    def _alarm_id(self, id):
        return f"{id}-alarm"

    # Job ID
    def _id_from_queue_url(self, url):
        return url.split("/")[-1].rstrip(".fifo")

    def _id_from_topic_arn(self, topic_arn):
        return topic_arn.split(":")[-1].rstrip("-sns")

    # Topic ID
    def _topic_arn_from_id(self, id):
        return f"arn:aws:sns:{self._region}:{self._account}:{self._topic_id(id)}"

    # Queue ID

    def _queue_url_from_id(self, id):
        return f"https://queue.amazonaws.com/{self._account}/{self._queue_id(id)}"

    def _queue_arn_from_url(self, url):
        return f"arn:aws:sqs:{self._region}:{self._account}:{url.split('/')[-1]}"

    def _error_queue_url_from_id(self, id):
        return f"https://queue.amazonaws.com/{self._account}/{self._queue_id(id, error=True)}"

    """
    Utility
    """

    def _create_queue(self, id, owner, error=False, tags={}, **kwargs):
        return sqs_client.create_queue(
            QueueName=self._queue_id(id, error),
            Attributes={
                "FifoQueue": "True",
                "MessageRetentionPeriod": "21600",  # 6 hours
                "VisibilityTimeout": "120",
                "ContentBasedDeduplication": "false",
                **kwargs,
            },
            tags={"Owner": owner, **tags},
        )

    """
    Public
    """

    def from_topic_arn(self, TopicArn):
        job_id = self._id_from_topic_arn(TopicArn)
        return self._queue_url_from_id(job_id)

    def list_tags(self, QueueUrl):
        return sqs_client.list_queue_tags(QueueUrl=QueueUrl)

    def create(
        self,
        Name,
        OwnerId,
        EventHandlerLambdaArn,
        MessageHandlerLambdaArn,
        Tags={},
        **kwargs,
    ):
        """
        Creates a new queue job with supporting queue, error queue, and
        event-mappings
        """

        assert Name
        assert OwnerId

        job_id = f"{Name}-{OwnerId.replace(' ', '')}-{repr(round(time()))}"

        queue_url = None
        finish_topic_arn = None

        try:
            """
            Resources
            """
            # Dead-letter error queue
            error_queue = self._create_queue(job_id, OwnerId, error=True)
            error_queue_url = error_queue["QueueUrl"]
            error_queue_arn = self._queue_arn_from_url(url=error_queue_url)

            print(error_queue_arn)
            queue = self._create_queue(
                id=job_id,
                owner=OwnerId,
                tags=Tags,
                RedrivePolicy=json.dumps(
                    {"deadLetterTargetArn": error_queue_arn, "maxReceiveCount": 1}
                ),
                **kwargs,
            )
            queue_url = queue["QueueUrl"]
            queue_arn = self._queue_arn_from_url(url=queue_url)

            # Must wait 1 second before using queue: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs_client.html#queue
            sleep(1)

            # Connect CloudWatch alarm to lambda
            sns_topic = sns_client.create_topic(
                Name=self._topic_id(job_id),
                Attributes={
                    "Policy": json.dumps(
                        {
                            "Version": "2008-10-17",
                            "Id": "QueueJobLambdaPolicy",
                            "Statement": [
                                {
                                    "Sid": "QueueJobLambdaExecutionAccess",
                                    "Effect": "Allow",
                                    "Principal": {"AWS": "*"},
                                    "Action": [
                                        "SNS:GetTopicAttributes",
                                        "SNS:SetTopicAttributes",
                                        "SNS:AddPermission",
                                        "SNS:RemovePermission",
                                        "SNS:DeleteTopic",
                                        "SNS:Subscribe",
                                        "SNS:ListSubscriptionsByTopic",
                                        "SNS:Publish",
                                    ],
                                    "Resource": "*",
                                }
                            ],
                        }
                    ),
                },
                Tags=[{"Key": "Owner", "Value": OwnerId}],
            )
            finish_topic_arn = sns_topic["TopicArn"]

            """
            Events
            """

            # Messages
            if MessageHandlerLambdaArn:
                lambda_client.create_event_source_mapping(
                    FunctionName=MessageHandlerLambdaArn,
                    EventSourceArn=queue_arn,
                    Enabled=True,
                    BatchSize=1,
                    FunctionResponseTypes=["ReportBatchItemFailures"],
                )

            # Empty
            alarm_name = self._alarm_id(job_id)
            cw_client.put_metric_alarm(
                AlarmName=alarm_name,
                AlarmDescription="Trigger QueueJob management lambda on SQS queue empty",
                AlarmActions=[finish_topic_arn],
                ActionsEnabled=True,
                MetricName="ApproximateNumberOfMessagesVisible",
                ComparisonOperator="LessThanOrEqualToThreshold",
                Namespace="AWS/SQS",
                Dimensions=[{"Name": "QueueName", "Value": self._queue_id(job_id)}],
                Threshold=0,
                Statistic="Minimum",
                Period=60,  # Minimum checking period
                EvaluationPeriods=1,
                TreatMissingData="ignore",
                Tags=[{"Key": "Owner", "Value": OwnerId}],
            )

            if EventHandlerLambdaArn:
                sns_client.subscribe(
                    TopicArn=finish_topic_arn,
                    Protocol="lambda",
                    Endpoint=EventHandlerLambdaArn,
                    ReturnSubscriptionArn=True,
                )

            return {
                "QueueUrl": queue_url,
                "FinishTopicArn": finish_topic_arn,
                "status": "Syncing",
            }

        except Exception as e:
            print(e)

            self.delete(QueueUrl=queue_url, TopicArn=finish_topic_arn)
            raise e

    def send(self, QueueUrl, Messages, request=""):
        """
        Send all messages to a queue job
        """
        queue_id = self._id_from_queue_url(QueueUrl)

        # Send messages in batches using index as the message ID
        for message_batch in chunk(list(enumerate(Messages)), self._batch_size):
            res = sqs_client.send_message_batch(
                QueueUrl=QueueUrl,
                Entries=[
                    {
                        "DelaySeconds": 0,
                        "MessageAttributes": {
                            "TransactionID": {
                                "DataType": "Number",
                                "StringValue": f"{i}",
                            },
                            "request": {
                                "DataType": "String",
                                "StringValue": f"{request}",
                            },
                        },
                        "MessageBody": (message),
                        "MessageGroupId": f"{queue_id}",
                        "MessageDeduplicationId": f"{queue_id}-{i}",
                        "Id": f"{queue_id}-{i}",
                    }
                    for i, message in message_batch
                ],
            )
            print(f"Messages {Messages} sent with res: {res}")

    def errors(self, QueueUrl):
        """
        Current status and errors in queue job
        """
        job_id = self._id_from_queue_url(QueueUrl)

        try:
            status = self.status(QueueUrl)
        except Exception:
            # Can't find the queue
            return {"Done": True}

        errors = sqs_client.receive_message(
            QueueUrl=self._error_queue_url_from_id(job_id),
            MaxNumberOfMessages=10,
            VisibilityTimeout=0,
        )

        return {
            **status,
            "InitialErrors": []
            if "Messages" not in errors
            else [error["Body"] for error in errors["Messages"]],
        }

    def status(self, QueueUrl):
        """
        Current status of the queue job
        """
        job_id = self._id_from_queue_url(QueueUrl)

        # Queue attributes
        attributes = sqs_client.get_queue_attributes(
            QueueUrl=QueueUrl,
            AttributeNames=[
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
                "RedrivePolicy",
                "CreatedTimestamp",
            ],
        )["Attributes"]

        # Error queue attributes
        error_attributes = sqs_client.get_queue_attributes(
            QueueUrl=self._error_queue_url_from_id(job_id),
            AttributeNames=["ApproximateNumberOfMessages"],
        )["Attributes"]

        num_being_processed = int(attributes["ApproximateNumberOfMessagesNotVisible"])
        num_remaining = int(attributes["ApproximateNumberOfMessages"])

        return {
            "StartTimestamp": int(attributes["CreatedTimestamp"]),
            "NumberOfMessagesBeingProcessed": num_being_processed,
            "Done": (num_being_processed + num_remaining) == 0,
            # ApproximateNumberOfMessages is exact for FIFO
            "NumberOfMessagesRemaining": num_remaining,
            # Failed messages in error queue
            "NumberOfErrors": int(error_attributes["ApproximateNumberOfMessages"]),
        }

    def delete(self, QueueUrl=None, TopicArn=None, MessageHandlerLambdaArn=None):
        """
        Delete the queue job with supporting resources and events
        """
        if not QueueUrl and not TopicArn:
            raise Exception("Need one of 'QueueUrl' or 'TopicArn'")

        job_id = (
            self._id_from_queue_url(QueueUrl)
            if QueueUrl
            else self._id_from_topic_arn(TopicArn)
        )

        queue_url = self._queue_url_from_id(job_id)
        queue_arn = self._queue_arn_from_url(queue_url)
        topic_arn = TopicArn if TopicArn else self._topic_arn_from_id(job_id)

        try:
            sqs_client.delete_queue(QueueUrl=self._error_queue_url_from_id(job_id))
        except Exception as e:
            print(f"Failed to delete error queues: {e}")

        try:
            sqs_client.delete_queue(QueueUrl=self._queue_url_from_id(job_id))
        except Exception as e:
            print(f"Failed to delete queue {QueueUrl}: {e}")

        # Remove subscriptions
        try:
            response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
            for subscription in response.get("Subscriptions", []):
                sns_client.unsubscribe(SubscriptionArn=subscription["SubscriptionArn"])
        except Exception as e:
            print(f"Failed to remove subscriptions: {e}")

        try:
            sns_client.delete_topic(TopicArn=topic_arn)
        except Exception as e:
            print(f"Failed to delete topic {topic_arn}: {e}")

        try:
            response = lambda_client.list_event_source_mappings(
                EventSourceArn=queue_arn,
                FunctionName=MessageHandlerLambdaArn,
                MaxItems=100,
            )
            for mapping in response.get("EventSourceMappings", []):
                lambda_client.delete_event_source_mapping(UUID=mapping["UUID"])
        except Exception as e:
            print(f"Failed to remove events: {e}")

        # Alarm
        try:
            cw_client.delete_alarms(AlarmNames=[self._alarm_id(job_id)])
        except Exception as e:
            print(f"Failed to delete alarm: {e}")

        return {"QueurUrl": queue_arn}
