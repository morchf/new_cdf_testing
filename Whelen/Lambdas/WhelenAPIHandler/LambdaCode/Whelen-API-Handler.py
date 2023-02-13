import boto3
import json
import os
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth

base_url = os.environ["CDF_URL"]
mac_address_api_url = os.environ["mac_address_api_url"]
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

session = boto3.session.Session(region_name=os.environ["AWS_REGION"])
dynamodb = boto3.setup_default_session(region_name=os.environ["AWS_REGION"])
dynamodb = boto3.resource("dynamodb")


agency_states_table = dynamodb.Table("agency-states.whelen")

client = boto3.client("sqs", region_name=os.environ["AWS_REGION"])
queue_url = client.get_queue_url(QueueName=os.environ["Whelen_SQS_Queue_Name"]).get(
    "QueueUrl"
)

lambda_client = boto3.client("lambda", region_name=os.environ["AWS_REGION"])


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


def lambda_handler(event, context):
    # Request will tell us what request the lambda is handling in this call.
    # Possible values:
    # 'importvehicles', 'change_preemption'
    print(f"event: {event}")
    body = json.loads(event["Records"][0].get("body"))
    request = body.get("request")
    global agency_guid  # We will update sync status for this agency.
    agency_guid = body.get("agency_guid")

    if request == "importvehicles":
        # 1. Get Collection of vehicles to import in CDF.
        # 2. Flag dynamo stating that the state is "syncing" now we have assets to import.
        # 3. Import those vehicles in CDF.
        # 4. Flag the agency in dynamo as "sync_completed" -> in import_delta.
        try:
            vehicle = body.get("vehicle")

            description = f'{vehicle.get("label")} {vehicle.get("vehicle_type")} {vehicle.get("make")} {vehicle.get("license_plate")}'

            agency_name = body.get("agency_name")
            agency_region = body.get("agency_region")
            print(f"description: {description}")
            print(f"agency_name: {agency_name}, agency region: {agency_region}")
            print(f"vehicle to import is: {vehicle}")
            create_device_in_CDF(vehicle, agency_region, agency_name, description)
            update_sync_status_for_agency(agency_guid, "synced")

            print(f"Assets imported for agency: {agency_guid}")

        except Exception as e:
            print(f"Error in processing the request to import vehicles: {e}")
            update_sync_status_for_agency(agency_guid, "failed_to_sync")

    elif request == "changepreemption":
        device_id = body.get("device_id")
        preemption_value = body.get("preemption_value")
        change_preemption(agency_guid, device_id, preemption_value)
        print("Changed preemption status for:", device_id)

    else:
        print("Invalid request")


##################################################
#   Helper method to change preemption of devices
##################################################
def change_preemption(agency_guid, device_id, preemption_value):
    """This method will poll Whelen for a specific agency and a specific device, and then goes to CDF and sets the preemption flag of each device to "active" or "inactive".

    Args:
        agency_guid (String): guid of agency, will use to get api endpoint of whelen.
        device_id (String): CDF's device_id which equates to Whelen's vehicle_id
        preemption_value (String): preemption value to change in CDF.
    """
    # 1. Check if this device exists in CDF, only then proceed.
    # 2. Find endpoint_url from Feature_persistence API.
    # 3. For the device_id, based on preemption value, send a call to Whelen.
    # 4. Change CDF flag "preemptionLicense" for each device based on preemption_value.

    # 1
    exists = device_in_cdf(device_id)
    if not exists:
        print("Device id {} does not exist in CDF, import it first".format(device_id))
        os._exit(os.EX_OK)  # No need to proceed ahead

    # 2
    whelen_api_information = load_agency_feature(agency_guid)

    # Check if the API information is empty or not.
    if not whelen_api_information:
        print("Agency requested not found in feature persistence API")
        os._exit(os.EX_OK)  # No need to proceed ahead.

    # We will send a call to Whelen based on this value.
    if preemption_value == "active":
        method = "POST"
    elif preemption_value == "inactive":
        method = "DELETE"
    else:
        os._exit(
            os.EX_OK
        )  # No need to proceed ahead since right now we are only handling requests for activating and inactivating preemption status.
    # 3
    signalWhelen(
        whelen_api_information["api_endpoint"],
        device_id,
        "/gtt/vehicles/",
        method,
        whelen_api_information["X-Api-Key"],
    )

    # 4
    change_preemption_flag_in_cdf(device_id, preemption_value, "PATCH")


def device_in_cdf(device_id) -> bool:
    """Returns a bool value if device exists in cdf or not

    Args:
        device_id (String): device id to check

    Returns:
        bool: true or false if device exists in cdf or not.
    """
    exists = False
    try:
        response = send_request(
            f"{base_url}/devices/" + device_id,
            "GET",
            os.environ["AWS_REGION"],
            headers=headers,
        )
        status_code = response.status_code
        if status_code != 200:
            print(f"Error in sending GET request to CDF for device {device_id}")
            os._exit(os.EX_OK)  # No need to proceed ahead.

        response = json.loads(response.content.decode("utf-8"))
        if response != "" and response:
            exists = True
    except Exception as e:
        print(f"Error in sending GET request to CDF for device {device_id} : {str(e)}")
        os._exit(os.EX_OK)  # No need to proceed ahead.
    return exists


def signalWhelen(whelen_api_endpoint, device_id, path, method, x_api_key):
    """This method will use api_endpoint to signal Whelen Cloud that a device is setup on the GTT side. (device = vehicle in whelen terms)

    Args:
        whelen_api_endpoint (String): Endpoint URL to poll Whelen
        device_id (String): Whelen's Vehicle ID
        path (String): The route to send request to.
        method (String): The API method using which we'll send request.
        x_api_key (String): The API Key for Whelen Authorization
    """
    # This method will be changed to Poll from Whelen API later.
    # For every device we will just simulate a 200 response.

    # It should go to the path: {whelen_api_endpoint}/path/device_id

    headers_whelen = headers
    headers_whelen["X-Api-Key"] = x_api_key

    whelen_api_endpoint += "/" + device_id
    response = send_request(
        url=whelen_api_endpoint,
        method=method,
        region_name=os.environ["AWS_REGION"],
        headers=headers_whelen,
    )
    status_code = response.status_code
    response = json.loads(response.content.decode("utf-8"))

    if status_code != 200 or "errorMessage" in response:
        # Record this errored device_id for log and terminate execution.
        print(
            f"Error from Whelen for: {device_id} using endpoint: {whelen_api_endpoint}and path: {path} and method: {method}"
        )
        os._exit(os.EX_OK)  # No need to proceed ahead.


def change_preemption_flag_in_cdf(device_id, preemption_value, method):
    """This method takes in a device_id and polls CDF using the given method to change preemptionLicense flag's value to preemption_value.

    Args:
        device_id (String): Device_id to change preemption of.
        preemption_value (String): value of the flag preemptionLicense to change.
        method (String): API Method to poll CDF with.
    """
    body = create_request_body(preemption_value)
    try:
        response = send_request(
            f"{base_url}/devices/" + device_id,
            method,
            os.environ["AWS_REGION"],
            headers=headers,
            params=body,
        )
        status_code = response.status_code
        if status_code != 200:
            print(f"Error in sending {method} request to CDF for vehicle {device_id}")
    except Exception as e:
        print(
            f"Error in sending {method} request to CDF for vehicle {device_id} : {str(e)}"
        )


def create_request_body(preemption_value) -> str:
    """This method creates a request body, which will be used to update the status of preemption on CDF side, based on the value of preemption_value.

    Args:
        preemeption_value: The value of preemptionLicense to change.

    Returns:
        response: json string of the body created.

    """

    return json.dumps({"attributes": {"preemptionLicense": preemption_value}})


#######################################
#   Helper methods for Import-Vehicles
#######################################


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
            Item={
                "AgencyGUID": agency_guid,
                "features": {"whelen": state},
            }
        )
    except Exception as e:
        print(f"Error updating sync status in dynamoDb: {e}")


def create_body(
    deviceId, agency_region, agency_name, description, addressMAC="67:56:45:34:23:12"
) -> str:

    """
    Create the body of a POST request to create a device in CDF.
    Args:
        deviceId (String):      device_id of the CDF device = Whelen vehicle_id
        agency_region (String): Region name of the agency that goes in CDF.
        agency_name (String):   Agency name of the agency that goes in CDF.
        addressMAC (String):    MAC Address of the device. Will fetch after API is developed.

    Returns:
        response: json string of the body created.
    """

    # "vehicle_id" in whelen vehicle -> "deviceId" in CDF device.
    # addressMAC will later be converted to be fetched from an API. -> story for this
    return json.dumps(
        {
            "groups": {"ownedby": ["/" + agency_region + "/" + agency_name]},
            "attributes": {
                "description": description,
                "serial": deviceId,
                "gttSerial": deviceId,
                "addressMAC": addressMAC,
                "uniqueId": deviceId,
                "integration": "Whelen",
                "preemptionLicense": "pending",
            },
            "category": "device",
            "templateId": "integrationcom",
            "state": "active",
            "deviceId": deviceId,
        }
    )


def create_device_in_CDF(vehicle, agency_region, agency_name, description):

    """
    Send a POST request to the CDF API Endpoint to create a device.
        Args:
            vehicle (dict): Whelen vehicle and its information.
            agency_region (String): Region name of the agency that goes in CDF.
            agency_name (String): Agency name of the agency that goes in CDF.

        Returns:
    """

    # 1. Map vehicle_id of whelen vehicle -> deviceId of CDF Device.
    # 2. Create a body, which will be sent in POST request of API.
    # 3. Send request to the CDF API to create a device.

    mac = send_request(
        mac_address_api_url,
        "GET",
        os.environ["AWS_REGION"],
        headers=headers,
    )
    macAddr = mac.content.decode("utf-8")

    body = create_body(
        vehicle.get("vehicle_id"), agency_region, agency_name, description, macAddr
    )

    print(f"body of the request is: {body}, base url: {base_url}")
    try:
        response = send_request(
            f"{base_url}/devices/",
            "POST",
            os.environ["AWS_REGION"],
            headers=headers,
            params=body,
        )
        status_code = response.status_code
        response = json.loads(response.content.decode("utf-8"))
        print(f"status_code is: {status_code}, response is: {response}")
        if status_code != 200 and "error" in response:
            print(f"Error in creating device in CDF: {response.get('error')}")
            update_sync_status_for_agency(agency_guid, "failed_to_sync")
            os._exit(os.EX_OK)  # No need to proceed ahead

    except Exception as e:
        print(f"Error in creating device in CDF: {e}")
        update_sync_status_for_agency(agency_guid, "failed_to_sync")
