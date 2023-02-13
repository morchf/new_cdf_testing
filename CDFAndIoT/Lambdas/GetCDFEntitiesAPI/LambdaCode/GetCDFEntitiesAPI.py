import os
import sys
import boto3
import json
import config_asset_lib
import requests
from requests_aws_sign import AWSV4Sign

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)

file_path = sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 3 * "/.."), "CDFBackend")
)

# Use values from config file
BASE_URL = config_asset_lib.BASE_URL
HEADERS = {
    "Accept": config_asset_lib.ACCEPT,
    "content-type": config_asset_lib.CONTENT_TYPE,
}


try:
    service = "execute-api"
    credentials = boto3.Session().get_credentials()
    aws_region = "us-east-1"
    auth = AWSV4Sign(credentials, aws_region, service)
except Exception as ex:
    print(ex)


def get_entities(query):
    print(f"****** get_entities = {query} *****")

    url = f"{BASE_URL}{query}"
    print(f"****** URL = {url} ******")

    r = requests.get(url, headers=HEADERS, auth=auth)
    print(f"get_entities response = {r.status_code}")
    print(f"get_entities response content = {r.content}")
    print(f"get_entities request headers = {r.request.headers}")

    return r.status_code, r.content


def lambda_handler(event, context):
    print(f"lambda_handler(): event = {event}")

    errorMessage = {
        "statusCode": 400,
        "body": "",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }

    successResponse = {
        "statusCode": 200,
        "body": {},
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }

    try:
        params = event["queryStringParameters"]
        query = params["0"]
        print(f"lambda_handler(): query = {query}")

        if query is not None:
            response = get_entities(query)
            load = json.loads(response[1])
            successResponse["body"] = json.dumps(load)
            return successResponse
        else:
            errorMessage["body"] = "Please choose entity: none selected"
            return errorMessage

    except Exception as ex:
        print(ex)
        errorMessage["body"] = ex
        return errorMessage
