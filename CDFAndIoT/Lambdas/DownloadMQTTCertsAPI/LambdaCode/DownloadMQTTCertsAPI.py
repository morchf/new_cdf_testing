import base64
import json
import os
from typing import Any, Dict

import boto3
from gtt.service.asset_library import AssetLibraryAPI

from gtt.data_model.asset_library import Communicator, Template

bucket_name = os.environ["CDF_CERTS_BUCKET_NAME"]

s3_client = boto3.client("s3")
asset_lib_api = AssetLibraryAPI()

default_headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def response(code: int, body: Any, headers: Dict[str, Any] = {}, **kwargs):
    return {
        "statusCode": code,
        "body": body,
        "headers": {**default_headers, **headers},
        **kwargs,
    }


def error(code: int, message: str):
    print(message)
    return response(code, json.dumps({"message": message}))


# Expects a URL path in the form /{serial}/{filename}
def lambda_handler(event: Dict[str, Any], context):
    print(f"lambda_handler(): event = {event}")

    # Parse request path
    path: str = event.get("path")
    if path is None:
        return error(400, "Unexpected null path. Event should be an API Gateway event")

    path_parts = path.strip("/").split("/")
    if len(path_parts) != 2:
        return error(
            400,
            "Unexpected path format. Expected: /{serial}/{filename}; Got: " + path,
        )

    serial = path_parts[0]
    filename = path_parts[1]

    # Get device from asset library
    try:
        device_id = asset_lib_api.find_device_id(
            template_id=Template.Communicator, serial=serial
        )
        device: Communicator = asset_lib_api.get_device(device_id)
    except ValueError as e:
        print(e)
        return error(404, f"Couldn't find Communicator device with serial: {serial}")

    s3_path = f"{device.region_name.upper()}/AGENCIES/{device.agency_name.upper()}/DEVICES/{serial}/{filename}"

    # Get file from S3
    try:
        res = s3_client.get_object(Bucket=bucket_name, Key=s3_path)
        zip_file = res["Body"].read()
    except Exception as e:
        print(e)
        return error(500, f"Couldn't retrieve file at: {s3_path}")

    # Return file as binary encoded
    return response(
        200,
        body=base64.b64encode(zip_file).decode("utf-8"),
        headers={
            "Content-Type": "application/zip",
        },
        isBase64Encoded=True,
    )
