import json
import os

import boto3
import redis

# Use values from env
BASE_URL = os.environ["SQS_BASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
REDIS_PORT = os.environ["REDIS_PORT"]

templates = {
    "AGENCY": "agency",
    "REGION": "region",
    "VEHICLE": "vehiclev2",
    "COMMUNICATOR": "communicator",
}

# set up authentication
try:
    service = "execute-api"
    credentials = boto3.Session().get_credentials()
    aws_region = os.environ["AWS_REGION"]

    # create an SQS Client
    sqs_client = boto3.client("sqs")

except Exception as e:
    print(f"error: {str(e)}")


def get_queue_URL():
    response = sqs_client.get_queue_url(QueueName="DeleteFromCacheQueue.fifo")
    print(f"Queue Url:{response['QueueUrl']}")
    return response["QueueUrl"]


def lambda_handler(event, context):
    try:
        print(f"Event Received: {event}")
        entity_dict = json.loads(event["Records"][0]["body"])
        print(f"Entity Dict: {entity_dict}")

        # first determine the template we are working with from the templates list
        # if template is an agency
        if entity_dict["templateId"] == templates["AGENCY"]:

            # Raise exception if the name, which is the device_id is not found
            if "name" in entity_dict:
                device_id = entity_dict["name"]
            else:
                raise Exception(
                    f"Error: No Device name found in agency template: {entity_dict}"
                )

            # check priority to see if EVP or TSP agency
            if "priority" in entity_dict["attributes"]:

                # This flow is handled by EVP DeleteFromCache Lambda. Leaving this here incase we need to merge flows in the future
                # EVP Agency flow
                # if entity_dict["attributes"]["priority"] == "High":
                #     print(
                #         f"EVP Entity found for {entity_dict['templateId']}. Deleting from Dynamo."
                #     )
                #     response_from_table = delete_from_dynamo(device_id)
                #     if response_from_table["ResponseMetadata"]["HTTPStatusCode"] != 200:
                #         raise Exception("Cache item could not be deleted.")

                # TSP Agency flow
                if entity_dict["attributes"]["priority"] == "Low":
                    print(
                        f"TSP Entity found for {entity_dict['templateId']}. Deleting from Redis."
                    )
                    response_from_table = delete_from_redis(device_id)
                    if response_from_table:
                        print(
                            f" Item with device ID: {device_id} deleted from TSP Cache."
                        )
                    else:
                        print(f"Could not delete item with device ID: {device_id}")
            else:
                raise Exception(
                    f"Error: Priority field missing from entity attributes: {entity_dict}"
                )

        # if template is a vehicle
        elif entity_dict["templateId"] == templates["VEHICLE"]:
            # Raise exception if the device_id is not found
            if "deviceId" in entity_dict:
                device_id = entity_dict["devices"]["out"]["installedat"][0]
            else:
                raise Exception(
                    f"Error: No Device name found in agency template: {entity_dict}"
                )

            # check priority to see if EVP or TSP agency
            if "priority" in entity_dict["attributes"]:

                # This flow is handled by EVP DeleteFromCache Lambda. Leaving this here incase we need to merge flows in the future
                # # EVP Agency flow
                # if entity_dict["attributes"]["priority"] == "High":
                #     print(
                #         f"EVP Entity found for {entity_dict['templateId']}. Deleting from Dynamo."
                #     )
                #     response_from_table = delete_from_dynamo(device_id)
                #     if response_from_table["ResponseMetadata"]["HTTPStatusCode"] != 200:
                #         raise Exception("Cache item could not be deleted.")

                # TSP Agency flow
                if entity_dict["attributes"]["priority"] == "Low":
                    print(
                        f"TSP Entity found for {entity_dict['templateId']}. Deleting from Redis."
                    )
                    response_from_table = delete_from_redis(device_id)
                    if response_from_table:
                        print(
                            f" Item with device ID: {device_id} deleted from TSP Cache."
                        )
                    else:
                        print(f"Could not delete item with device ID: {device_id}")
            else:
                raise Exception(
                    f"Error: Priority field missing from entity attributes: {entity_dict}"
                )

        # if template is a communicator
        elif entity_dict["templateId"] == templates["COMMUNICATOR"]:
            # Raise exception if the device_id is not found
            if "deviceId" in entity_dict:
                device_id = entity_dict["deviceId"]
            else:
                raise Exception(
                    f"Error: No Device name found in agency template: {entity_dict}"
                )

            # check model of communicator
            # If 2101, then TSP flow
            if entity_dict["attributes"]["model"] == "2101":
                print(
                    f"TSP Entity found for {entity_dict['templateId']}. Deleting from Redis for deviceID: {device_id}."
                )
                response_from_table = delete_from_redis(device_id)
                if response_from_table:
                    print(f" Item with device ID: {device_id} deleted from TSP Cache.")
                else:
                    print(f"Item with device ID: {device_id} not present in cache.")

            # This flow is handled by EVP DeleteFromCache Lambda. Leaving this here incase we need to merge flows in the future
            # If 2100, then EVP flow
            # elif entity_dict["attributes"]["model"] == "2100":
            #     print(
            #         f"EVP Entity Received for {entity_dict['templateId']}. Deleting from Dynamo for deviceID: {device_id}."
            #     )
            #     response_from_table = delete_from_dynamo(device_id)
            #     if response_from_table["ResponseMetadata"]["HTTPStatusCode"] != 200:
            #         raise Exception("Cache item could not be deleted.")
            #     print(f"Deletion from Dynamo successful for {device_id}")

            # If model is MP-70 send delete command to both Dynamo and Redis.
            # Only performed to Redis here because EVP Lambdas handle the DyanmoDB flow

            elif entity_dict["attributes"]["model"] == "MP-70":
                print(
                    f"EVP Entity Received for {entity_dict['templateId']}. Deleting from Redis for deviceID: {device_id}."
                )
                response_from_table = delete_from_redis(device_id)

                if response_from_table:
                    print(f" Item with device ID: {device_id} deleted from TSP Cache.")
                else:
                    print(f"Item with device ID: {device_id} not present in cache.")

        # if template is a region
        elif entity_dict["templateId"] == templates["REGION"]:
            print("Template is a region template. No deletion performed.")

        else:
            raise Exception("Did not receive message from SQS")

    except Exception as e:
        print(f"Error: {e}")


#  creating an SQS boto3 resource to receive a message from SQS
def receive_message(BASE_URL):
    try:
        sqs_message = sqs_client.receive_message(
            QueueUrl=BASE_URL,
            MaxNumberOfMessages=1,
            MessageAttributeNames=["All"],
        )
        return sqs_message
    except Exception:
        raise Exception("Did not receive message from SQS.")


# This flow is handled by EVP DeleteFromCache Lambda. Leaving this here incase we need to merge flows in the future
# create and initialise resources to delete the item from the caching table
# def delete_from_dynamo(device_id):
#     dynamodb = boto3.resource("dynamodb")
#     table_name = "CachingTable"
#     cache = dynamodb.Table(table_name)
#     # device_id = sqs_message["Messages"][0]["Body"].split(",")[0]

#     if cache:
#         if device_id:
#             get_response = cache.get_item(Key={"ID": device_id})
#             print(f"Get from table: {get_response}")
#             response_from_table = cache.delete_item(Key={"ID": device_id})
#         else:
#             raise Exception("No device ID in call to delete_from_dynamo")
#     else:
#         raise Exception(f"Error connecting to dynamo: {cache}")
#     if response_from_table:
#         print(f"Response from Cache: {response_from_table}")
#         return response_from_table
#     else:
#         raise Exception("No response from dynamo. Cache item might not be deleted.")


def delete_from_redis(device_id):
    print("Deleting from Redis for TSP Entity...")
    try:
        redis_cache = redis.Redis(
            host=REDIS_URL, port=REDIS_PORT, db=0, decode_responses=True
        )

        # Create the redis key
        redis_key = f"cdf_cache:{device_id}"

        # delete({key}) returns number of items deleted
        deletion_response = redis_cache.delete(redis_key)
        if deletion_response > 0:
            print(f"{deletion_response} items were deleted from Redis.")
            return True
        else:
            print(f"Entity not present in Redis cache. Response: {deletion_response}")
            return False
    except Exception as RedisDeletionException:
        print(f"Exception occurred: {RedisDeletionException}")
