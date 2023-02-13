import boto3
from boto3.dynamodb.conditions import Attr
import json
from decimal import Decimal
import logging

logging.basicConfig(level=logging.DEBUG)

dyanmoTable = boto3.resource("dynamodb", region_name="us-east-1").Table("globalMacVps")


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)


def lambda_handler(event, context):
    """[summary]
    Return all the elements that belong to one agency

    Arguments:
        event {[json]} -- [customer name]

    Returns:
        [list] -- [list of elements form dynamodb for one particular agency]
    """
    inps = event["queryStringParameters"]
    logging.debug(inps["customerName"])
    # check for bad input variable
    if not isinstance(inps["customerName"], str):
        return {
            "statusCode": 400,
            "body": "Invalid input parameters",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    response = dyanmoTable.scan(
        FilterExpression=Attr("customerName").eq(inps["customerName"])
    )["Items"]
    if len(response) != 0:
        return {
            "statusCode": 200,
            "body": json.dumps(response, default=default),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    elif len(response) == 0:
        return {
            "statusCode": 404,
            "body": inps["customerName"] + " name not found",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
