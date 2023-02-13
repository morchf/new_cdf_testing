import boto3
import itertools
from boto3.dynamodb.conditions import Attr
import logging

logging.basicConfig(level=logging.DEBUG)


def lambda_handler(event, context):
    """[summary]
    Function will be invoked every 30 minutes to call a ssm run commnand and
    if the run command has already been called on the ec2 server, the new run
    command will be blocked
    Arguments:
        event {[json]} -- [customerName]
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
    # check if there are any commands running on the ec2 servers,
    #  if yes dont issue the command
    runningSSMCmnds = [
        ec2s["InstanceIds"]
        for ec2s in boto3.client("ssm", region_name="us-east-1").list_commands(
            Filters=[
                {"key": "DocumentName", "value": "AWS-RunShellScript"},
                {"key": "Status", "value": "InProgress"},
            ]
        )["Commands"]
    ]
    if (
        len(
            [
                item
                for item in ec2_instances
                if item in list(itertools.chain.from_iterable(runningSSMCmnds))
            ]
        )
        == 0
    ):
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
                    "sudo /usr/bin/python3 DockerCreate.py",
                ],
                "workingDirectory": ["/home/ec2-user"],
                "executionTimeout": ["3500"],
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
            InstanceIds=ec2_instances,
        )
