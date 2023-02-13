import boto3
from boto3.dynamodb.conditions import Attr
import json
import time
import pandas as pd


# helper functions
def get_role_arn(sts_client):
    account_id = sts_client.get_caller_identity()["Account"]
    return "arn:aws:iam::" + account_id + ":role/ModemTestRole"


def get_policy_arn(sts_client):
    account_id = sts_client.get_caller_identity()["Account"]
    return "arn:aws:iam::" + account_id + ":policy/ModemTestPolicy"


def get_table_arn(table_name, dynamodb_client):
    response = dynamodb_client.describe_table(TableName=table_name)
    return response["Table"]["TableArn"]


# Create DynamoDB Table
def create_message_table(dynamodb):

    table = dynamodb.create_table(
        TableName="ModemTestTable",
        KeySchema=[
            {"AttributeName": "timeStamp", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "topic", "KeyType": "RANGE"},  # Sort key
        ],
        AttributeDefinitions=[
            {"AttributeName": "timeStamp", "AttributeType": "S"},
            {"AttributeName": "topic", "AttributeType": "S"},
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )
    print("DynamoDB table ModemTestTable created")
    return table


# Create IAM Role
def create_iam_role(iam_client, sts_client, dynamodb_client):
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {"Service": "iot.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    iam_client.create_role(
        RoleName="ModemTestRole", AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    print("IAM role ModemTestRole created")

    table_arn = get_table_arn("ModemTestTable", dynamodb_client)

    role_policy_document = {
        "Version": "2012-10-17",
        "Statement": {
            "Effect": "Allow",
            "Action": "dynamodb:PutItem",
            "Resource": table_arn,
        },
    }

    iam_client.create_policy(
        PolicyName="ModemTestPolicy", PolicyDocument=json.dumps(role_policy_document)
    )
    print("IAM policy ModemTestPolicy created")
    policy_arn = get_policy_arn(sts_client)
    iam_client.attach_role_policy(
        PolicyArn=policy_arn,
        RoleName="ModemTestRole",
    )
    print("ModemTestPolicy attached to ModemTestRole")


# Create ModemTestDynamoDB rule
def create_iot_rule(iam_client, sts_client, iot_client):
    role_arn = get_role_arn(sts_client)
    response = iot_client.create_topic_rule(
        ruleName="ModemTestDynamoDB",
        topicRulePayload={
            "sql": "SELECT * FROM '+/messages/json'",
            "ruleDisabled": False,
            "awsIotSqlVersion": "2016-03-23",
            "actions": [
                {
                    "dynamoDB": {
                        "tableName": "ModemTestTable",
                        "roleArn": role_arn,
                        "hashKeyField": "timeStamp",
                        "hashKeyValue": "${timestamp()}",
                        "hashKeyType": "STRING",
                        "rangeKeyField": "topic",
                        "rangeKeyValue": "${topic()}",
                        "rangeKeyType": "STRING",
                        "payloadField": "message",
                    },
                },
            ],
        },
    )
    print("IoT rule ModemTestDynamoDB created")
    return response


# Prescreen Modem Message
def prescreen_message(vehicle_serialNum, dynamodb):

    table = dynamodb.Table("ModemTestTable")

    for serialNum in vehicle_serialNum:
        topic = serialNum + "/messages/json"
        response = table.scan(FilterExpression=Attr("topic").eq(topic))
        # validate topic
        res = validate_topic(response)
        if not res:
            return False, topic + " not exist"

        # validate contents
        res, error = validate_content(response)
        if not res:
            return False, error

        return True, "PASS Prescreen Test. Topic and message content are correct"


def validate_topic(response):
    if len(response["Items"]) == 0:
        return False
    return True


def validate_content(response):
    item = response["Items"][0]
    message = item["message"]
    contents = list(message.values())[0]

    gspd = contents.get("atp.gspd")
    if gspd is None:
        return False, "atp.gspd not existed or out of range"
    # gstt = contents.get("atp.gstt")
    # if gstt is None:
    #     return False, "atp.gstt not existed or out of range"
    gpi = contents.get("atp.gpi")
    if gpi is None or gpi > 31 or gpi < 0:
        return False, "atp.gpi not existed or out of range"
    # gqal = contents.get("atp.gqal")
    # if gqal is None:
    #     return False, "atp.gqal not existed or out of range"
    ghed = contents.get("atp.ghed")
    if ghed is None:
        return False, "atp.ghed not existed or out of range"
    # gsat = contents.get("atp.gsat")
    # if gsat is None:
    #     return False, "atp.gsat not existed or out of range"
    glon = contents.get("atp.glon")
    if glon is None or glon > 180 or glon < -180:
        return False, "atp.glon not existed or out of range"
    glat = contents.get("atp.glat")
    if glat is None or glat > 180 or glat < -180:
        return False, "atp.glat not existed or out of range"

    return True, ""


# Postscreen Modem Message
def postscreen_message(vehicle_serialNum, dynamodb):

    dynamodb_table = dynamodb.Table("ModemTestTable")

    df = pd.DataFrame(
        columns=[
            "serialNum",
            "max_glitch",
            "mean_glitch",
            "count_glitch",
            "pct_miss",
            "mean_trans_time",
        ]
    )
    for serialNum in vehicle_serialNum:
        topic = serialNum + "/messages/json"
        response = dynamodb_table.scan(
            FilterExpression=Attr("topic").eq(topic))
        items = response["Items"]

        for item in items:
            message = item["message"]
            item["actual_timestamp"] = list(message.keys())[0]

        table = pd.DataFrame(items)
        table = table.sort_values("actual_timestamp")
        del table["message"]

        table["last_timestamp"] = table["actual_timestamp"].shift(1)
        table = table.iloc[1:]
        table["glitch"] = table["actual_timestamp"].astype(int) - table[
            "last_timestamp"
        ].astype(int)

        table["trans_time"] = table["timeStamp"].astype(float) / 1000 - table[
            "actual_timestamp"
        ].astype(float)

        # Calculate gltich between messages
        max_glitch = table["glitch"].max()
        mean_glitch = table["glitch"].mean()
        count_glitch = table[table.glitch > 1].shape[0]

        print(table[table.glitch > 1])

        # Calculate percentage of seconds missed
        not_missed = table.shape[0]
        total_sec = (
            int(table["actual_timestamp"].values[-1])
            - int(table["actual_timestamp"].values[0])
            + 1
        )

        print("not_missed: " + str(not_missed))
        print("total_sec: " + str(total_sec))
        print("first timestamp: " + str(table["actual_timestamp"].values[0]))
        print("last timestamp: " +
              str(table["actual_timestamp"].values[-1]) + "\n")

        pct_miss = (total_sec - not_missed) / total_sec

        # Calculate trans time between real timestamp and iot timestamp
        mean_trans_time = table["trans_time"].mean()

        df = df.append(
            {
                "serialNum": serialNum,
                "max_glitch": max_glitch,
                "mean_glitch": mean_glitch,
                "count_glitch": count_glitch,
                "pct_miss": pct_miss,
                "mean_trans_time": mean_trans_time,
            },
            ignore_index=True,
        )

    return df


# delete rules
def delete_iot_rule(iot_client):
    iot_client.delete_topic_rule(ruleName="ModemTestDynamoDB")
    print("ModemTestDynamoDB IoT rule deleted.")


# delete dynamoDB table
def delete_dynamodb_table(dynamodb):
    table = dynamodb.Table("ModemTestTable")
    table.delete()
    print("ModemTestTable table deleted.")


# delete policy
def delete_policy(iam_client, sts_client):
    policy_arn = get_policy_arn(sts_client)
    iam_client.detach_role_policy(
        PolicyArn=policy_arn, RoleName="ModemTestRole")
    iam_client.delete_policy(PolicyArn=policy_arn)
    print("ModemTestPolicy IAM policy deleted.")


# delete role
def delete_role(iam_client):
    iam_client.delete_role(RoleName="ModemTestRole")
    print("ModemTestRole IAM role deleted.")


def modem_test(vehicle_serialNum, listen_time=1, region_name="us-east-1"):
    # Connect with IoT, dynamoDB, STS, IAM
    sts_client = boto3.client("sts", region_name=region_name)
    iot_client = boto3.client("iot", region_name=region_name)
    iam_client = boto3.client("iam", region_name=region_name)
    dynamodb = boto3.resource("dynamodb", region_name)
    dynamodb_client = boto3.client("dynamodb", region_name=region_name)
    print("======================Setting Up Environment======================\n")
    create_message_table(dynamodb)
    create_iam_role(iam_client, sts_client, dynamodb_client)
    create_iot_rule(iam_client, sts_client, iot_client)

    print("======================Prescreen test start======================")
    time.sleep(10)
    prescreen_res, msg = prescreen_message(vehicle_serialNum, dynamodb)
    print(prescreen_res)
    print(msg)

    if not prescreen_res:
        print("FAILED Prescreen Test")
        print("Error: " + msg)
        print("======================Prescreen test end======================\n")

        print("======================Cleaning Up Resources======================\n")
        delete_iot_rule(iot_client)
        delete_dynamodb_table(dynamodb)
        delete_policy(iam_client, sts_client)
        delete_role(iam_client)

        return False, msg

    else:
        # If pass prescreen, sleep listen_time minutes, invoke postscreen test
        print("======================Prescreen test end======================\n")
        print("======================Postscreen test start====================")
        print("wait for " + str(listen_time) + " minutes......")
        time.sleep(60 * listen_time)
        postscreen_table = postscreen_message(vehicle_serialNum, dynamodb)
        print("===================Modem postscreen test result=================\n")
        print(postscreen_table)

        print("======================Cleaning Up Resources======================\n")
        delete_iot_rule(iot_client)
        delete_dynamodb_table(dynamodb)
        delete_policy(iam_client, sts_client)
        delete_role(iam_client)

        return True, postscreen_table


if __name__ == "__main__":
    # Config
    listen_time = 1
    region_name = "us-east-1"
    vehicle_serialNum = ["SimDevice0101", "SimDevice0102"]

    # run the test
    modem_test(vehicle_serialNum, listen_time, region_name)
