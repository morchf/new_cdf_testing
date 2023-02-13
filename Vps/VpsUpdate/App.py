import boto3
import json
from boto3.dynamodb.conditions import Attr
import re

import logging

logging.basicConfig(level=logging.DEBUG)


dyanmoTable = boto3.resource("dynamodb", region_name="us-east-1").Table("globalMacVps")
client = boto3.client("dynamodb", region_name="us-east-1")


def getEc2Id(serverName, region):
    ec2_client = boto3.client("ec2", region_name=region)
    custom_filter = [
        {"Name": "tag:serverName", "Values": [serverName]},
        {"Name": "instance-state-name", "Values": ["running"]},
    ]
    response = ec2_client.describe_instances(Filters=custom_filter)
    ec2_instances = [
        item["Instances"][0]["InstanceId"] for item in response["Reservations"]
    ]
    return ec2_instances[0]


def updateVps(dockerName, status, version, tableName="globalMacVps"):
    """[summary]
    Change the docker status according to user needs( START/STOP/RESTART/DELETE)
    Args:
        dockerName ([string]): [docker/VPS name]
        status ([string]): [could be any one these status "START/STOP/RESTART/DELETE"]
        tableName (str, optional): [Default name of the dynmaoDB table].
        Defaults to "globalMacVps".
    Returns:
        [dict]: [json object returned to the api calls]
    """
    successMessage = {
        "statusCode": 200,
        "body": dockerName + " device status successfully updated",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
    response = dyanmoTable.scan(FilterExpression=Attr("VPS").eq(dockerName))["Items"]
    if len(response) < 1:
        return {
            "statusCode": 404,
            "body": dockerName + " name not found",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    elif len(response) > 1:
        return {
            "statusCode": 500,
            "body": dockerName
            + " name ambiguous.  Found multiple VPS with name "
            + dockerName,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    if (
        status in ["ACTIVE", "INACTIVE", "RESTART"]
        and response[0]["deviceStatus"] != status
    ):
        dockPrimary = int(response[0]["primaryKey"])
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "Key": {"primaryKey": {"N": str(dockPrimary)}},
                        "TableName": "globalMacVps",
                        "UpdateExpression": "SET deviceStatus =:devstatus ",
                        "ExpressionAttributeValues": {":devstatus": {"S": status}},
                    }
                }
            ]
        )

    if status in ["YES", "NO"] and response[0]["markToDelete"] != status:
        dockPrimary = int(response[0]["primaryKey"])
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "Key": {"primaryKey": {"N": str(dockPrimary)}},
                        "TableName": "globalMacVps",
                        "UpdateExpression": "SET markToDelete =:devstatus ",
                        "ExpressionAttributeValues": {":devstatus": {"S": status}},
                    }
                }
            ]
        )

    try:
        dockerVersion = response[0]["dockerImage"].split(":")[1]
    except:
        dockerVersion = None
    if (
        dockerVersion is not None
        and version is not None
        and (dockerVersion != version or version == "latest")
    ):
        print("Upgrading docker version")
        serverProperties = (
            boto3.resource("dynamodb", region_name="us-east-1")
            .Table("codeBuildDeploy")
            .scan(
                FilterExpression=Attr("customerName").eq(response[0]["customerName"])
            )["Items"]
        )
        logGrpSNSFAIL = "GTT-VPS-FAILS"
        ssm_client = boto3.client(
            "ssm", region_name=serverProperties[0]["serverRegion"]
        )
        ec2Id = getEc2Id(response[0]["serverName"], serverProperties[0]["serverRegion"])
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
                    "sudo /usr/bin/python3 UpgradeVps.py " + dockerName + "=" + version,
                ],
                "workingDirectory": ["/home/ec2-user"],
                "executionTimeout": ["1000"],
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
            InstanceIds=[ec2Id],
        )

    return successMessage


def lambda_handler(event, context):
    """[summary]
    updates the docker to do make the status active, inactive or restart
    Arguments:
        event {[json]} -- [The vps name for which the status has to changed]

    Raises:
        Exception: [exception will be raised if the vps state is not valid]
    """
    jsonInputs = json.loads(event["body"])
    logging.debug(jsonInputs)
    if not (
        isinstance(jsonInputs["dockerStatus"], str)
        and isinstance(jsonInputs["VPSName"], str)
    ) or (
        jsonInputs.get("VPSVersion", None) is not None
        and not isinstance(jsonInputs["VPSVersion"], str)
    ):
        return {
            "statusCode": 400,
            "body": "Invalid input parameters",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    if jsonInputs["dockerStatus"] not in ["ACTIVE", "INACTIVE", "RESTART", "YES", "NO"]:
        return {
            "statusCode": 400,
            "body": "Invalid VPS device status('ACTIVE':- Keep VPS/Docker in "
            "running state ,'INACTIVE':- Keep VPS/Docker in stop state, 'YES':- "
            "Delete the Docker or 'RESTART':-VPS/Docker to restart)",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    if (
        jsonInputs.get("VPSVersion", None) is not None
        and re.match(
            r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$)|^latest$", jsonInputs["VPSVersion"]
        )
        is None
    ):
        return {
            "statusCode": 400,
            "body": "Invalid VPS version number.  Should be in the format xxx.xxx.xxx or 'latest'",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    return updateVps(
        jsonInputs["VPSName"],
        jsonInputs["dockerStatus"],
        jsonInputs.get("VPSVersion", None),
    )
