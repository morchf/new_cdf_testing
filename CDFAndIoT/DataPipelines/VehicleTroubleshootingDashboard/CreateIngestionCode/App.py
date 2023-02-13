import uuid
import os
import boto3


def getDataSetId(name):
    qs = boto3.client("quicksight")
    response = qs.list_data_sets(
        AwsAccountId=boto3.client("sts").get_caller_identity().get("Account")
    )
    for i in response["DataSetSummaries"]:
        if i["Name"] == name:
            return i["DataSetId"]


def lambda_handler(event, context):
    qs = boto3.client("quicksight")
    qs.create_ingestion(
        DataSetId=getDataSetId(os.environ["QuicksightDatasetName"]),
        IngestionId=str(uuid.uuid4()),
        AwsAccountId=boto3.client("sts").get_caller_identity().get("Account"),
    )
