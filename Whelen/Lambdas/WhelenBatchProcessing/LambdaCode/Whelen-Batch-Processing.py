import os
import json
import boto3

from util.messages import create_messages
from util.http import ok, error, not_found
from util.email import Client as EmailClient
from services.queue_job import Client as QueueJob

from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth


aws_account = boto3.client("sts").get_caller_identity().get("Account")
aws_region = os.environ["AWS_REGION"]

queue_job = QueueJob(aws_account, aws_region)
email_subject = "Batch Whelen Devices Load Results"
email_client = EmailClient(os.getenv("SNS_REPORT_TOPIC_ARN"), email_subject)

owner = "Whelen-API-Handler"
base_url = os.environ["CDF_URL"]

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

session = boto3.session.Session(region_name=os.environ["AWS_REGION"])
dynamodb = boto3.setup_default_session(region_name=os.environ["AWS_REGION"])
dynamodb = boto3.resource("dynamodb")

agency_states_table = dynamodb.Table("agency-states.whelen")


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(session.get_credentials(), "execute-api", region_name).add_auth(
        request
    )  # noqa: E501
    return URLLib3Session().send(request.prepare())


def parse_event(event):
    params = {}
    # SNS notification
    if (
        "Records" in event
        and len(event["Records"]) != 0
        and "EventSource" in event["Records"][0]
        and event["Records"][0]["EventSource"] == "aws:sns"
    ):
        params = {**event, "type": "finish"}
    # Query-string params
    elif "body" in event and event.get("body") is not None:
        # Create event.
        body = json.loads(event.get("body"))
        agency_guid = body.get("agency_guid")
        devices = body.get("devices")
        params["devices"] = devices
        params["agency_guid"] = agency_guid
        params["type"] = "create"
        params["task"] = "changepreemption"

    elif "queryStringParameters" in event and "type" in event["queryStringParameters"]:
        params = {**event, **event["queryStringParameters"]}

    elif (
        ("/importvehicles" in event["path"])
        and ("POST" in event["httpMethod"])
        and ("agency_guid" in event["queryStringParameters"])
    ):
        # We can send a request to import whelen vehicles.
        params = {**event, **event["queryStringParameters"]}
        params["task"] = "importvehicles"

    else:
        params = "Invalid request received"

    return params


def complete_job(message_handler_lambda_arn, queue_url=None, topic_arn=None):
    queue_url = queue_url if queue_url else queue_job.from_topic_arn(topic_arn)
    errors = queue_job.errors(QueueUrl=queue_url)

    # Email from queue tag
    tags = queue_job.list_tags(QueueUrl=queue_url)["Tags"]

    # Send message
    if "OwnerEmail" in tags:
        email_client.send_report(tags["OwnerEmail"], errors)

    # Delete queue
    queue_job.delete(
        QueueUrl=queue_url,
        TopicArn=topic_arn,
        MessageHandlerLambdaArn=message_handler_lambda_arn,
    )


def lambda_handler(event, context):
    """
    Manages a queue job for long running Whelen API calls. Handles event
    types--create, delete, status, and finish--from three different sources

    - Manually: Designated by the 'type' field
    - API call: Pass in 'type' query-string parameter
    - SNS event: 'finish'

    The 'create' event assumes an 'owner' attribute in the query parameters to
    uniquely identify a job creation source

    Must add the below headers to the 'create' requests
    - Content-Type: multipart/form-data
    - Accept: multipart/form-data

    Must add the file and extension to the 'create' form data
    - file: File data
    - type: Extension
    """
    params = parse_event(event)
    attached_lambda_arn = os.environ["LAMBDA_HANDLER_ARN"]
    lambda_arn = context.invoked_function_arn

    if "task" in params and params["task"] == "changepreemption":
        # Change preemption
        messages = None
        try:
            if not params["devices"]:
                return error({"errorMessage": "Received Devices list empty!"})
            if (
                not params["agency_guid"]
                or params["agency_guid"] == ""
                or not is_valid_guid(params["agency_guid"])
            ):
                return error({"errorMessage": "Invalid agency guid received!"})
            info = {}
            info["devices"] = params["devices"]
            info["agency_guid"] = params["agency_guid"]
            info["request"] = params["task"]
            messages = create_messages(info)
        except Exception as e:
            error_message = (
                f"Failed on message create: {messages}"
                if messages
                else f"Failed on template parsing: {messages}"
            )
            print(f"Error: Issue in parsing template: {error_message} with: {e}")
            os._exit(os.EX_OK)  # No need to proceed ahead.

        # Create queue
        queue_url = None
        try:
            response = queue_job.create(
                Name="WhelenSQSQueue",
                OwnerId=owner,
                EventHandlerLambdaArn=lambda_arn,
                MessageHandlerLambdaArn=attached_lambda_arn,
            )
            queue_url = response["QueueUrl"]

            # Populate queue
            queue_job.send(
                QueueUrl=queue_url, Messages=messages, request="changepreemption"
            )

        except Exception as e:
            print(e)
            queue_job.delete(
                QueueUrl=queue_url, MessageHandlerLambdaArn=attached_lambda_arn
            )
            print("Error: Issue starting the Queue Job")
            os._exit(os.EX_OK)  # No need to proceed ahead.

        return ok(response, statusCode=202)

    if "type" in params and params["type"] == "status":
        assert params["queue_url"]
        try:
            status = queue_job.status(QueueUrl=params["queue_url"])
        except Exception:
            return not_found()

        if status["Done"]:
            complete_job(
                queue_url=params["queue_url"],
                message_handler_lambda_arn=attached_lambda_arn,
            )
        return ok(status)

    if "type" in params and params["type"] == "finish":
        complete_job(
            topic_arn=params["Records"][0]["Sns"]["TopicArn"],
            message_handler_lambda_arn=attached_lambda_arn,
        )
        return ok()

    if "type" in params and params["type"] == "delete":
        return ok(
            queue_job.delete(
                params["queue_url"], MessageHandlerLambdaArn=attached_lambda_arn
            )
        )

    if "task" in params and params["task"] == "importvehicles":
        # to store queue messages.
        messages = []
        # Read the agency guid from the request.
        global agency_guid
        agency_guid = params.get("queryStringParameters").get("agency_guid")
        if agency_guid == "" or not agency_guid or not is_valid_guid(agency_guid):
            return error({"errorMessage": "Invalid or empty GUID received!"})

        # For a given agency, To send a message we need to do the following things:
        # 1. Get devices from Whelen
        # 2. Get devices from CDF
        # 3. Compute delta of missing vehicles (collection of device_ids)
        # 4. Create message for each device_id in delta
        # 5. Dump the messages to SQS queue using long running queue job.

        # 1
        (
            whelen_vehicles,
            agency_region,
            agency_name,
        ) = get_whelen_vehicles_for_agency(agency_guid)

        if agency_region == "" or agency_name == "":
            return error({"errorMessage": "Invalid GUID received!"})

        # 3
        cdf_device_ids = get_deviceIds_from_cdf(agency_region, agency_name)

        # 4
        delta = get_delta(whelen_vehicles, cdf_device_ids)

        # 5
        if len(delta) != 0:
            # Sync only if there are assets to import.
            info = {}
            info["devices"] = delta
            info["agency_region"] = agency_region
            info["agency_name"] = agency_name
            info["agency_guid"] = agency_guid
            info["request"] = "importvehicles"
            messages = create_messages(info)

            # Create queue
            queue_url = None
            try:
                response = queue_job.create(
                    Name="WhelenSQSQueue",
                    OwnerId=owner,
                    EventHandlerLambdaArn=lambda_arn,
                    MessageHandlerLambdaArn=attached_lambda_arn,
                )
                queue_url = response["QueueUrl"]

                # Populate queue
                queue_job.send(
                    QueueUrl=queue_url, Messages=messages, request="importvehicles"
                )

            except Exception as e:
                queue_job.delete(
                    QueueUrl=queue_url, MessageHandlerLambdaArn=attached_lambda_arn
                )
                return error({"errorMessage": f"Issue in starting the queue Job {e}!"})
            # Update agency-states.whelen table.
            update_sync_status_for_agency(agency_guid, "syncing")
            return ok(response, statusCode=202)
        else:
            return error({"errorMessage": "No assets available to import!"})

    return error({"errorMessage": "Unknown Request Received!"})


#######################################
#   Helper methods for Import-Vehicles
#######################################


def is_valid_guid(agency_guid) -> bool:
    """Given an agency guid, check if its present in feature persistence. Then allow the script to proceed if it is..

    Args:
        agency_guid (String): GUID of the agency

    Returns:
        bool: true if guid in feature persistence
    """
    present = False
    try:
        url = (
            os.environ["feature_persistence_url"]
            + "?AgencyGUID="
            + agency_guid.upper()
            + "&FeatureName=whelen"
        )
        response = send_request(
            url, method="GET", region_name=os.environ["AWS_REGION"], headers=headers
        )
        status_code = response.status_code
        if status_code == 200:
            present = True

    except Exception as e:
        print(f"Error: in fetching information from Feature Persistence: {e}")
    return present


def load_agency_feature(agency_guid) -> dict:
    """
    Poll API "agency_features" to get information about a specific agency and its features.
    Args:
        agency_guid (String): Poll Feature Persistence API to get an AgencyGUID's features.

    Returns:
        response: Agency's features and attributes as a dictionary.
    """
    agency_feature = {}
    try:
        url = (
            os.environ["feature_persistence_url"]
            + "?AgencyGUID="
            + agency_guid.upper()
            + "&FeatureName=whelen"
        )
        response = send_request(
            url, method="GET", region_name=os.environ["AWS_REGION"], headers=headers
        )
        status_code = response.status_code
        response = json.loads(response.content.decode("utf-8"))
        # only store attributes if the agency contains Whelen's
        if status_code == 200:
            agency_feature = response.get("Feature")
        else:
            print("Agency GUID not found in Feature Persistence")
            os._exit(os.EX_OK)  # No need to proceed ahead.

    except Exception as e:
        print(f"Error: in fetching information from Feature Persistence: {e}")
    return agency_feature


def get_agency_info_from_cdf(agency_guid):
    """
    Get {region_name, agency_name} from CDF for a given 'agency_guid'.
        Args:
            agency_guid (String) :  The GUID of a particular agency in CDF.

        Returns:
            response: region_name (String), agency_name (String)
    """
    region_name = ""
    agency_name = ""
    try:
        url = f"{base_url}/search?type=agency"
        response = send_request(url, "GET", os.environ["AWS_REGION"], headers=headers)
        status_code = response.status_code
        if status_code != 200:
            print("Error: No Agencies received from CDF")
            os._exit(os.EX_OK)  # No need to proceed ahead.
        response = json.loads(response.content.decode("utf-8"))
        agencies = response.get("results")
        for agency in agencies:
            if agency_guid == agency.get("attributes").get("agencyID"):
                groupPath = agency.get("groupPath").split("/")
                region_name = groupPath[1]
                agency_name = groupPath[2]
    except Exception as e:
        print(f"Error in getting all agencies from CDF: {e}")

    return region_name, agency_name


def get_whelen_vehicles_for_agency(agency_guid):
    """
    Get all vehicles and their information from Whelen.
    Args:
        agency_guid (String) : The guid of the agency, corresponding to the one in the API "agency_features".

    Returns:
        response: list of vehicles and their information.
                        eg: [{'model': '', 'label': '', 'vehicle_id': 'whelencom0', 'vin': '', 'device_id': '', 'vehicle_type': '', 'mfg_year': '', 'license_plate': '', 'make': '', gtt_preemption: ''},{}]
                    - region_name,
                    - agency_name
    """
    vehicles = []
    agency_region = ""
    agency_name = ""

    whelen_api_information = load_agency_feature(agency_guid)
    if whelen_api_information:
        agency_region, agency_name = get_agency_info_from_cdf(agency_guid)
        # Else access the vehicles from the file for now.
        # Will be changed to poll the Whelen API Endpoint.
        vehicles = get_whelen_vehicles(
            whelen_api_information["api_endpoint"],
            whelen_api_information["accessKey"],
            whelen_api_information["X-Api-Key"],
        )
    return vehicles, agency_region, agency_name


def get_whelen_vehicles(api_endpoint_url, accessKey, x_api_key) -> list:
    """GET a collection of Whelen Vehicles and its information by polling Whelen's API Endpoint.

    Args:
        api_endpoint (String): Endpoint URL of Whelen
        accessKey (String): The accessKey of a particular agency
        x_api_key (String): Authorization API Key of Whelen

    Returns:
        list: List of Whelen Vehicles and its attributes
    """
    # We will use a GET Method to get a collection of Whelen vehicles.

    # Make a copy of headers for whelen's request
    vehicles = []
    try:
        headers_whelen = headers
        headers_whelen["X-Api-Key"] = x_api_key

        api_endpoint_url += "?accessKey=" + accessKey
        method = "GET"

        response = send_request(
            url=api_endpoint_url,
            method=method,
            region_name=os.environ["AWS_REGION"],
            headers=headers_whelen,
        )
        response = json.loads(response.content.decode("utf-8"))
        vehicles = response.get("message").get("vehicles")

    except Exception as e:
        print(f"Error in getting data from whelen: {e}")

    return vehicles


def get_deviceIds_from_cdf(agency_region, agency_name) -> list:
    """
    Get a list of all device_ids from CDF.
        Args:
            region_name (String): The region_name that goes in the CDF endpoint.
            agency_name (String): The agency_name that goes in the CDF endpoint.

        Returns:
            response: list of all device_ids for a specific agency from CDF.
                       eg: [whelencom1, whelencom2, ...]
    """
    device_ids = []
    try:
        url = f"{base_url}/groups/%2F{agency_region}%2F{agency_name}/members/devices"
        response = send_request(url, "GET", os.environ["AWS_REGION"], headers=headers)
        status_code = response.status_code
        if status_code != 200:
            print("Error: in loading devices from CDF")
            update_sync_status_for_agency(agency_guid, "failed_to_sync")
            os._exit(os.EX_OK)  # No need to proceed ahead.
        response = json.loads(response.content.decode("utf-8"))
        devices = response.get("results")
        device_ids = [device["deviceId"] for device in devices]

        # We just need vehicle ids to compare.
        # We import vehicles whose ids are not in this list.
    except Exception as e:
        print(f"Error in loading devices from CDF: {e}")
        update_sync_status_for_agency(agency_guid, "failed_to_sync")

    return device_ids


def get_delta(whelen_vehicles, cdf_device_ids) -> list:

    """
    Find all missing Whelen vehicles in CDF.
        Args:
            whelen_vehicles (list): list of Whelen vehicles.
            cdf_device_ids (list): list of CDF device_ids.

        Returns:
            response: list of all whelen vehicles for a specific agency not present in CDF.
    """

    seen = set(cdf_device_ids)
    return [item for item in whelen_vehicles if item.get("vehicle_id") not in seen]


def update_sync_status_for_agency(agency_guid, state):

    """
    Flag DynamoDb table for this agency to indicate the sync-status for this agency.
        Args:
            agency_guid (String): guid of agency to flag in dynamo.
            state (String): Indicating what's the syncing status?
                            - unsynced -> have unsynced vehicles to import
                            - syncing  -> lambda is processing the sync request
                            - synced.  -> lambda successfully imported vehicles in CDF for the agency.
                            - failed_to_sync -> There is an error in importing vehicles in CDF.

        Returns:
    """

    # Do it at the end after vehicles are created in CDF successfully.
    # This can be used to show message to the user on UI.
    # Indicating that agency's CDF side is in sync with Whelen.
    try:
        agency_states_table.put_item(
            Item={"AgencyGUID": agency_guid, "features": {"whelen": state}}
        )
    except Exception as e:
        print(f"Error updating sync status in dynamoDb: {e}")
