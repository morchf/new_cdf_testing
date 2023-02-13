import json
import logging
import math
import os
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_random

logging.basicConfig(level=logging.DEBUG)

dynamoRegion = "us-east-1"
dynamodbTable = "globalMacVps"
codeBuildDynamo = "codeBuildDeploy"

client = boto3.client("dynamodb", region_name="us-east-1")
cdbuild = boto3.client("codebuild", region_name="us-east-1")
cdproject = os.environ["CODE_BUILD_PROJECT"]


def ec2Name(idN, divCnt, customerName):
    """[summary]
    Function will take integer , max count of docker and customer name

    Arguments:
        idN {[integer]} -- [integer]
        divCnt {[integer]} -- [maximum number dockers to be placed in EC2 server]
        customerName {[string]} -- [customer name]

    Returns:
        [type] -- [servername]
    """
    return customerName + str(math.ceil(idN / divCnt))


def returnDynamoLST(customerName, dynamodbTable="globalMacVps"):
    """[summary]
    Return the list of servers with the number of records present in the dynamodb
    Arguments:
        customerName {[String]} -- [Agency name of the customer]

    Returns:
        [list] -- [returns list with server name number of active VPS]
    """
    getLIST = client.scan(
        TableName=dynamodbTable,
        ProjectionExpression="serverName,markToDelete",
        FilterExpression="customerName = :custNm",
        ExpressionAttributeValues={":custNm": {"S": customerName}},
    )["Items"]
    response = [
        {
            "serverName": item["serverName"]["S"],
            "markToDelete": item["markToDelete"]["S"],
        }
        for item in getLIST
    ]
    return sorted(
        list(
            Counter(
                token["serverName"]
                for token in response
                if token["markToDelete"] != "YES"
            ).items()
        )
    )


def retDateCode(deviceName):
    """[summary]
    Function will return two letter date code which
    will be combined with the device name. The wkstring logic
    is designed by gtt.

    Arguments:
        deviceName {[String]} -- [Enter the device name]

    Returns:
        [string] -- [device name combined with the date code]
    """
    yrString = dict(zip(list(range(2019, 2034)), list(map(chr, range(76, 92)))))
    wkString = dict(zip(list(range(14, 367, 14)), list(map(chr, range(65, 91)))))
    currentYR = datetime.now().timetuple().tm_year
    currentDT = datetime.now().timetuple().tm_yday
    weekCode = wkString[
        list(range(14, 367, 14))[bisect_left(list(range(14, 367, 14)), currentDT)]
    ]
    return deviceName + yrString[currentYR] + weekCode


def dynamoPreInsert(
    newIntMac,
    newVPS,
    devicePrefix,
    dockerNum,
    customerName,
    dynamodbTable,
    devStatus="ACTIVE",
    markDel="NO",
    vpsavailability="AVAILABLE",
    agencyId="",
):
    """[summary]
        The function will insert the data into the dynamodb. Data to the
         dynamo consists of newmac unique address,
        new unique serial number, customer name and the servername for the dockers
    Arguments:
        newIntMac {[Integer]} -- [Current max integer]
        newVPS {[String]} -- [Current serial number]
        devicePrefix {[String]} -- [Device Prefix]
        dockerNum {[Integer]} -- [Docker location in the server name]
        customerName {[String]} -- [Customer name]
        dynamodbTable {[String]} -- [dynamo db table]

    Keyword Arguments:
        devStatus {str} -- [Represents the docker status]
         (default: {'ACTIVE'})  #INACTIVE: Stop the container
        markDel {str} -- [Docker removal] (default: {'NO'}) #YES: Marked for delete

    """
    macInsert = str(newIntMac + 1)
    vpsInsert = retDateCode(devicePrefix) + (str(int(newVPS[-4:]) + 1).zfill(4))
    formatmac = format(newIntMac + 1, "x").upper()
    newformatmac = ":".join([formatmac[i : i + 2] for i in range(0, len(formatmac), 2)])
    if (int(newVPS[-4:]) + 1 < 9999) & (int(newVPS[-4:]) + 1 > 0):
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "Key": {"primaryKey": {"N": "11111"}},
                        "TableName": dynamodbTable,
                        "UpdateExpression": "SET macCode =:newmac , VPS = :newvps ",
                        "ConditionExpression": "VPS <> :newvps",
                        "ExpressionAttributeValues": {
                            ":newmac": {"N": macInsert},
                            ":newvps": {"S": vpsInsert},
                        },
                    }
                },
                {
                    "Put": {
                        "Item": {
                            "primaryKey": {"N": macInsert},
                            "GTTmac": {"S": newformatmac},
                            "VPS": {"S": vpsInsert},
                            "deviceStatus": {"S": devStatus},
                            "markToDelete": {"S": markDel},
                            "customerName": {"S": customerName},
                            "vpsAvailability": {"S": vpsavailability},
                            "serverName": {"S": ec2Name(dockerNum, 250, customerName)},
                            "agencyId": {"S": agencyId},
                        },
                        "TableName": dynamodbTable,
                        "ConditionExpression": "primaryKey <> :pk",
                        "ExpressionAttributeValues": {":pk": {"N": macInsert}},
                        "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
                    }
                },
            ]
        )
        return True


@retry(
    wait=wait_random(0, 3) + wait_random(1, 3),
    stop=stop_after_attempt(10),
    reraise=True,
)
def dynamoInsert(devicePrefix, dockerNum, customerName, dynamodbTable, agencyId):
    """[summary]
        Function passes parameters to insert the data to the predynamoinsert functions
    Arguments:
        devicePrefix {[String]} -- [device prefix]
        dockerNum {[Integer]} -- [docker number]
        customerName {[String]} -- [customer name]
        dynamodbTable {[String]} -- [dynamodb table name]

    Raises:
        Exception: [Exception when you try to insert the duplicate data]
    """
    try:
        dynamoGetItem = client.get_item(
            TableName=dynamodbTable,
            Key={"primaryKey": {"N": "11111"}},
            ProjectionExpression="primaryKey,macCode,VPS",
        )
        newIntMac = int(dynamoGetItem["Item"]["macCode"]["N"])
        newVPS = dynamoGetItem["Item"]["VPS"]["S"]
        dynamoPreInsert(
            newIntMac,
            newVPS,
            devicePrefix,
            dockerNum,
            customerName,
            dynamodbTable,
            agencyId=agencyId,
        )
        # response=
        # if response['Response']==500: raise Exception(response['Message'])
    except ClientError as error:
        logging.debug(error)
        raise Exception(error)


def propertiesFetch(agencyName):
    """[summary]
    Return the items from the dynamoDb
    Arguments:
        agencyName {[string]} -- [customerName]

    Returns:
        [list] -- [list of elements from the dynamoDB]
    """
    return client.scan(
        TableName=codeBuildDynamo,
        FilterExpression="customerName = :custNm",
        ExpressionAttributeValues={":custNm": {"S": agencyName}},
    )["Items"][0]


def lambda_handler(event, context):
    jsonInputs = json.loads(event["body"])
    req = jsonInputs["number"]
    devicePrefix = jsonInputs["deviceprefix"]
    customerName = jsonInputs["customer"]
    agencyId = jsonInputs["agencyId"].lower()
    customerRegion = jsonInputs["region"]
    logging.debug("%s/%s", customerRegion, customerName)
    # customer region and s3loaction are declared later in the code
    mes = []  # for failed messages
    # check for bad input variable
    if not (
        isinstance(req, int)
        and isinstance(devicePrefix, str)
        and isinstance(customerName, str)
    ):
        return {
            "statusCode": 400,
            "body": "Invalid input parameters",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    # Test if resource is availabe in the codebuild dyanmo db table
    try:
        getProperties = client.get_item(
            TableName=codeBuildDynamo, Key={"customerName": {"S": customerName}}
        )["Item"]
        try:
            lastInvoke = getProperties.get("lastInvokeVpscreate")["S"]
        except Exception:
            lastInvoke = (datetime.now(timezone.utc) - timedelta(minutes=20)).strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        # Restrict the api call to atleast 15 minutes(api might trigger codebuild,
        #  which might take upto 15m minutes)
        if (
            datetime.now(timezone.utc).replace(tzinfo=None)
            - datetime.strptime(lastInvoke, "%d/%m/%Y %H:%M:%S")
        ).total_seconds() < 900:
            return {
                "statusCode": 429,
                "body": "Too many request. Try after 15 minutes",
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }
    except KeyError as error:
        logging.exception(error)
        return {
            "statusCode": 404,
            "body": f'{jsonInputs["customer"]} name not found',
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    # accessing dynmaoDB to check the number of devices created in a two week period and
    # it should not exceed more then 9999 in a span of two weeks
    dynamoGetItem = client.get_item(
        TableName=dynamodbTable,
        Key={"primaryKey": {"N": "11111"}},
        ProjectionExpression="VPS",
    )
    reqVl = (
        9998 - int(dynamoGetItem["Item"]["VPS"]["S"][-4:]) - req
    )  # request validation

    if reqVl < 100:
        return {
            "statusCode": 429,
            "body": "Max limit for biweekly exceeded. NO action performed",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    else:
        dynamo_ec2_grp_lst = returnDynamoLST(customerName)
        numberinc = req - (
            len(dynamo_ec2_grp_lst) * 250 - sum([x[1] for x in dynamo_ec2_grp_lst])
        )
        listN = list(
            range(
                (len(dynamo_ec2_grp_lst) * 250) + 1,
                (len(dynamo_ec2_grp_lst) * 250) + 1 + numberinc,
            )
        )
        listM = [
            list(
                range(
                    1 + x[1] + (int(x[0].split(customerName)[-1]) - 1) * 250,
                    int(x[0].split(customerName)[-1]) * 250 + 1,
                )
            )
            for x in dynamo_ec2_grp_lst
        ]
        dockerNum = sorted(listN + sum(listM, []))[:req]
        for i in dockerNum:
            try:
                dynamoInsert(devicePrefix, i, customerName, dynamodbTable, agencyId)
            except Exception as errormessage:
                mes.append(errormessage)
                if len(mes) > 2:
                    break
        # variables are declared here, because the validation for these
        #  variables happens before thier assignments
        # Customer server region
        aws_region = propertiesFetch(customerName)["serverRegion"]["S"]

        # S3 location to deploy the customer cloudformation template
        s3_location = [
            d["S"].split("##")[1]
            for d in propertiesFetch("GTT")["S3Location"]["L"]
            if d["S"].split("##")[0] == aws_region
        ][0]
        ec2_client = boto3.client("ec2", region_name=aws_region)
        dynamo_ec2_grp = list(
            map(
                lambda item: [item[0], item[1], {"instTypeAct": "m5a.xlarge"}]
                if item[1] > 100
                else [item[0], item[1], {"instTypeAct": "m5a.large"}],
                returnDynamoLST(customerName),
            )
        )
        # start the codebuild project if the ec2 capacity is not sufficient
        #  to deploy the number of docker
        # code build project accepts three environment parameters, that should
        #  be pass as the  startcodebuild execution
        # the ec2 expansion or scalability depends upon only on either existing
        #  ec2 servers which are on running state or no servers for the agency

        try:
            for items in dynamo_ec2_grp:
                custom_filter = [
                    {"Name": "tag:serverName", "Values": [items[0]]},
                    {"Name": "instance-state-name", "Values": ["running"]},
                ]
                instanceType = ec2_client.describe_instances(Filters=custom_filter)[
                    "Reservations"
                ][0]["Instances"][0]["InstanceType"]
                if (items[2]["instTypeAct"]) != instanceType:
                    cdbuild.start_build(
                        projectName=cdproject,
                        environmentVariablesOverride=[
                            {
                                "name": "customerName",
                                "value": customerName,
                                "type": "PLAINTEXT",
                            },
                            {
                                "name": "regionName",
                                "value": customerRegion,
                                "type": "PLAINTEXT",
                            },
                            {
                                "name": "awsRegion",
                                "value": aws_region,
                                "type": "PLAINTEXT",
                            },
                            {
                                "name": "S3Location",
                                "value": s3_location,
                                "type": "PLAINTEXT",
                            },
                        ],
                    )
                    logging.debug("CODDEBUILD INITIATED")
                    break
        except Exception:
            try:
                cdbuild.start_build(
                    projectName=cdproject,
                    environmentVariablesOverride=[
                        {
                            "name": "customerName",
                            "value": customerName,
                            "type": "PLAINTEXT",
                        },
                        {
                            "name": "regionName",
                            "value": customerRegion,
                            "type": "PLAINTEXT",
                        },
                        {
                            "name": "awsRegion",
                            "value": aws_region,
                            "type": "PLAINTEXT",
                        },
                        {
                            "name": "S3Location",
                            "value": s3_location,
                            "type": "PLAINTEXT",
                        },
                    ],
                )
                logging.debug("CODDEBUILD INITIATED")
            except Exception:
                pass
        # update the timestamp in codebuilddynamo table
        client.update_item(
            TableName=codeBuildDynamo,
            Key={"customerName": {"S": customerName}},
            UpdateExpression="SET lastInvokeVpscreate = :time",
            ExpressionAttributeValues={
                ":time": {"S": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")}
            },
        )
        return {
            "statusCode": 200,
            "body": "Successfully provisioned required number of VPS",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
