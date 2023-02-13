import json
import boto3
import os
import logging
from CEI_Logging import post_log
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth

url = os.environ["CDF_URL"]
client = boto3.client("iot-data", os.environ["AWS_REGION"])
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

# TBD - leverage CDF_layer for request instead.
def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    return URLLib3Session().send(request.prepare())


def configurationHandler(event, context):
    """handles the incoming agency configuration call from the API

    Args:
        event (dictionary): configuration message body
        context (dictionary): call metadata (aws required structure, unused in function)

    Returns:
        string: results of operation
    """
    try:
        print(url)
        config_args = event
        # handle for lambda proxy conversion -
        if "body" in event:
            config_args = json.loads(event["body"])

        # url construction vars

        site_id = config_args["siteId"]
        agency_id = config_args["agencyId"]
        url_action = f"groups/%2F{site_id}%2F{agency_id}"
        url_complete = f"{url}/{url_action}"

        # masking internal 's - CDF will choke if we don't
        for item in config_args:
            config_args[item] = str(config_args[item]).replace("'", "|||")

        config = {
            "attributes": {
                "CEIUnitTypeConfig": config_args["unitTypeConfig"],
                "CEIUnitIDConfig": config_args["unitIDConfig"],
                "CEIIncidentTypeConfig": config_args["incidentTypeConfig"],
                "CEIIncidentStatusConfig": config_args["incidentStatusConfig"],
                "CEIIncidentPriorityConfig": config_args["incidentPriorityConfig"],
                "CEIUnitStatusConfig": config_args["unitStatusConfig"],
            }
        }

        updateCall = json.dumps(config).replace("'", '"').replace("|||", "'")
        logging.info(f"Update Call = {updateCall}")

        patch_result = send_request(
            url_complete,
            "PATCH",
            os.environ["AWS_REGION"],
            params=updateCall,
            headers=headers,
        )

        response_json = {
            "statusCode": 200,
            "body": f"Configuration for {config_args['siteId']}:{config_args['agencyId']} updated",
        }
        if patch_result.status_code == 404:
            response_json = {
                "statusCode": 400,
                "body": f"Error updating {config_args['siteId']}:{config_args['agencyId']} - Agency/siteId not found",
            }
        response = {
            "statusCode": response_json.get("statusCode"),
            "body": json.dumps(response_json),
        }

        # logDat
        post_log(
            site_id,
            agency_id,
            None,
            None,
            "Info",
            "Configuration Message",
            "Configuration",
            json.dumps(config_args),
        )
        print(response)
        return response
    except KeyError as e:
        response_json = {"statusCode": 400, "body": f"Message Format Error - {e}"}
        response = {"statusCode": 400, "body": json.dumps(response_json)}
        print(response)
        return response
    except Exception as e:
        response_json = {
            "statusCode": 500,
            "body": f"{e.__class__.__name__} Error - {e}",
        }
        response = {"statusCode": 500, "body": json.dumps(response_json)}
        return response
