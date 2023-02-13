import json
import boto3

from util.messages import create_report

sns_client = boto3.client("sns")


class Client:
    def __init__(self, topic_arn, SUBJECT):
        self._topic_arn = topic_arn
        self._SUBJECT = SUBJECT

    def _create_message(self, errors, to_email):
        report = create_report(
            errors["StartTimestamp"],
            errors["InitialErrors"],
        )

        return {
            "To": to_email,
            "Subject": self._SUBJECT,
            "Body": report,
        }

    def subscribe_to_reports(self, email):
        # Check for existing subscription
        next_token = True
        while next_token:
            response = (
                sns_client.list_subscriptions_by_topic(
                    TopicArn=self._topic_arn, NextToken=next_token
                )
                if isinstance(next_token, str)
                else sns_client.list_subscriptions_by_topic(TopicArn=self._topic_arn)
            )

            next_token = response["NextToken"] if "NextToken" in response else None

            for subscription in response["Subscriptions"]:
                if (
                    subscription["Protocol"] == "email"
                    and subscription["Endpoint"] == email
                ):
                    return

        sns_client.subscribe(
            TopicArn=self._topic_arn,
            Protocol="email",
            Endpoint=email,
            Attributes={"FilterPolicy": json.dumps({"email": [email]})},
        )

    def send_report(self, email, errors):
        message = self._create_message(errors, to_email=email)
        sns_client.publish(
            TopicArn=self._topic_arn,
            Message=message["Body"],
            Subject=message["Subject"],
            MessageAttributes={
                "email": {"DataType": "String", "StringValue": email},
            },
        )
