# noqa: F632

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    try:
        table = dynamodb.Table("IntegrationMACRecord")
        response = table.query(
            ConsistentRead=True, KeyConditionExpression=Key("MACRecord").eq("MACRecord")
        )

        value = response["Items"][0]["currentIdx"] + 1
        if value == 30000:
            value = 60001

        rehex = hex(int("CC69B0000000", 16) + int(value))[2:14]

        MACAddress = ""
        idx = 0
        for x in rehex:
            idx = idx + 1
            MACAddress = MACAddress + x
            if idx % 2 == 0 and len(MACAddress) < 17:
                MACAddress = MACAddress + ":"

        response = table.update_item(
            Key={
                "MACRecord": "MACRecord",
            },
            UpdateExpression="SET currentIdx = :val0",
            ExpressionAttributeValues={":val0": value},
            ReturnValues="UPDATED_NEW",
        )

        response = {"statusCode": 200, "body": MACAddress.upper()}
        return response

    except Exception as e:
        response = {"statusCode": 500, "body": f"[ERROR] - {e}"}
        return response
