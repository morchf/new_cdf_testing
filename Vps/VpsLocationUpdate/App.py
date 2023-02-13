import boto3
from boto3.dynamodb.conditions import Attr
import logging

logging.basicConfig(level=logging.DEBUG)


def lambda_handler(event, context):
    """[summary]
    Function will be invoked from the vpscmswrite with the customer name parameter
    Function will run ssm commands the server which will updates the location details
    in the efs
    Arguments:
        event {[json]} -- [customer name]
    """
    ecs_names = event["customerName"]
    logging.debug(ecs_names)
    serverProperties = (
        boto3.resource("dynamodb", region_name="us-east-1")
        .Table("codeBuildDeploy")
        .scan(FilterExpression=Attr("customerName").eq(ecs_names))["Items"]
    )
    ssm_client = boto3.client("ssm", region_name=serverProperties[0]["serverRegion"])
    ec2_client = boto3.client("ec2", region_name=serverProperties[0]["serverRegion"])
    custom_filter = [
        {"Name": "tag:aws:cloudformation:stack-name", "Values": [ecs_names]},
        {"Name": "instance-state-name", "Values": ["running"]},
    ]
    response = ec2_client.describe_instances(Filters=custom_filter)
    ec2_instances = [
        item["Instances"][0]["InstanceId"] for item in response["Reservations"]
    ]
    logGrpSNSFAIL = "GTT-VPS-FAILS"
    ssm_client.send_command(
        DocumentName="AWS-RunShellScript",
        TimeoutSeconds=30,
        Parameters={
            "commands": [
                "sudo -u ec2-user git config --global credential.helper"
                " '!aws codecommit credential-helper $@'",
                "sudo -u ec2-user git config --global credential.UseHttpPath true",
                "if cd GTTVPSDEPLOYMENT; then sudo -u ec2-user git pull; else sudo"
                " -u ec2-user git clone https://"
                "git-codecommit.us-east-1.amazonaws.com/v1/repos/GTTVPSDEPLOYMENT;"
                " cd GTTVPSDEPLOYMENT; fi",
                "sudo /usr/bin/python3 DockerLocation.py --customerName "
                + str(ecs_names),
            ],
            "workingDirectory": ["/home/ec2-user"],
            "executionTimeout": ["3600"],
        },
        ServiceRoleArn="arn:aws:iam::"
        + boto3.client("sts").get_caller_identity().get("Account")
        + ":role/GTTVPSINSTANCEPROFILE",
        NotificationConfig={
            "NotificationArn": "arn:aws:sns:"
            + serverProperties[0]["serverRegion"]
            + ":"
            + boto3.client("sts").get_caller_identity().get("Account")
            + ":"
            + logGrpSNSFAIL,
            "NotificationEvents": ["TimedOut", "Cancelled", "Failed"],
            "NotificationType": "Command",
        },
        CloudWatchOutputConfig={
            "CloudWatchLogGroupName": logGrpSNSFAIL,
            "CloudWatchOutputEnabled": True,
        },
        InstanceIds=[ec2_instances[0]],
    )
