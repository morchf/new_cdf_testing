import os
import boto3
from botocore.parsers import JSONParser
from requests_aws_sign import AWSV4Sign
import redis
import config_asset_lib


QueueName = "PostLiveStatusOfIntersectionsPerAgency"

# set up authentication
try:
    service = "execute-api"
    credentials = boto3.Session().get_credentials()
    aws_region = os.environ["AWS_REGION"]
    auth = AWSV4Sign(credentials, aws_region, service)

    # create an SQS and an Elasticache Client and let it stay warm between executions
    sqs_client = boto3.client("sqs")
    elasticache_client = boto3.client("elasticache")


except Exception as e:
    print(f"error: {str(e)}")


def lambda_handler(event, context):
    try:
        print(f"Event received: {event}")

        # get the QueueURL and use the URL to retreive the message from the SQS
        QueueURL = get_queue_URL(QueueName)
        message = receive_message(QueueURL)

        # check if the message contains a gttSerial number and state (prevent KeyErrors), add the same as items in the message to be sent to Redis
        if message and message["message"]:
            if (
                message["message"]["attributes"]["gttSerial"]
                and message["message"]["state"]
            ):
                gttSerial = message["message"]["attributes"]["gttSerial"]
                status = message["message"]["state"]
                data_to_elasticache = {
                    f"{gttSerial}": f"{status}",
                    "message": {message["message"]},
                }
                post_data_to_elasticache(data_to_elasticache, gttSerial, status)
            else:
                raise Exception("GTT Serial Number/Status missing in call to Lambda")

        else:
            raise Exception("No 'message' key present in call to Lambda")

    except Exception as e:
        print(f"error: {str(e)}")


# get the URL of the QueueName set at the top of the file
def get_queue_URL(QueueName):
    try:
        response = sqs_client.get_queue_url(QueueName=QueueName)
        print(f"Queue Url:{response['QueueUrl']}")
        return response["QueueUrl"]
    except Exception:
        raise ("Could not get queue URL")


# receive messages from the QueueURL passed and returns result
def receive_message(QueueURL):
    try:
        sqs_message = sqs_client.receive_message(
            QueueUrl=QueueURL, MessageAttributeNames=["All"]
        )
        return sqs_message
    except Exception:
        raise Exception("Did not receive message from SQS.")


# post the data to Redis elasticache, with the GTT Serial Number of the device as the key
def post_data_to_elasticache(data_to_elasticache, gttSerial):
    try:
        CLUSTER_ID = config_asset_lib.CLUSTER_ID
        response = elasticache_client.describe_cache_clusters(
            CacheClusterId=CLUSTER_ID, MaxRecords=1
        )

        response = JSONParser.parse(response)
        CLUSTER_URL = response["CacheClusters"][0]["ConfigurationEndpoint"]["Address"]
        port = response["CacheClusters"][0]["ConfigurationEndpoint"]["Port"]

        r = redis.Redis(host=CLUSTER_URL, port=port, db=0)

        r.set(gttSerial, data_to_elasticache)

    except Exception as e:
        print(f"error: {str(e)}")
