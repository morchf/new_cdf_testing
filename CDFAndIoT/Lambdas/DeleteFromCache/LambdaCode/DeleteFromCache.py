import json

import boto3

templates = {
    "AGENCY": "agency",
    "REGION": "region",
    "VEHICLE": "vehiclev2",
    "COMMUNICATOR": "communicator",
    "PHASESELECTOR": "phaseselector",
}
table_name = "CachingTable"


try:
    sqs_client = boto3.client("sqs")
    dynamodb = boto3.resource("dynamodb")
    cache = dynamodb.Table(table_name)
except Exception as e:
    print(f"error: {str(e)}")


def lambda_handler(event, context):
    try:
        print("Event Received: ", event)
        entity_dict = json.loads(event["Records"][0]["body"])

        # For deleting from cache if the template is agency then entity name is
        # used a key else device ID.
        # For region template there is nothing to delete.
        cache_key = ""
        if entity_dict["templateId"] == templates["AGENCY"]:
            if "name" in entity_dict:
                cache_key = entity_dict["name"]
            else:
                raise Exception(
                    f"Error: No device name found in agency template: {entity_dict}"
                )
        # There might be multiple devices associated with a vehicle. We are deleting one device at a time.
        elif entity_dict["templateId"] == templates["VEHICLE"]:
            if len(entity_dict["devices"]["out"]["installedat"]) > 0:
                for key in entity_dict["devices"]["out"]["installedat"]:
                    delete_data_from_cache(key)
            else:
                raise Exception(
                    f"Error: No device id found in vehicle template: {entity_dict}"
                )

        elif entity_dict["templateId"] == templates["COMMUNICATOR"]:
            if "deviceId" in entity_dict:
                cache_key = entity_dict["deviceId"]
            else:
                raise Exception(
                    f"Error: No Device name found in communicator template: {entity_dict}"
                )

        elif entity_dict["templateId"] == templates["REGION"]:
            print("Template is a region template. No deletion performed.")

        elif entity_dict["templateId"] == templates["PHASESELECTOR"]:
            print("Template is a phase template. No deletion performed.")

        else:
            raise Exception("Did not receive message from SQS with a valid template.")

        if cache_key:
            delete_data_from_cache(cache_key)
        return 200

    except Exception as e:
        print(f"Error: {e}")


def delete_data_from_cache(cache_key):
    response_from_table = {}
    if cache_key:
        response_from_table = cache.delete_item(Key={"ID": cache_key})
        print(f"Response from Cache: {response_from_table}")
    if response_from_table.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        print("Cache delete successful")
    else:
        raise Exception("Cache item could not be deleted.")
