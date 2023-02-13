import boto3
import os


def lambda_handler(event, context):
    client = boto3.client("apigateway")
    pipeline = boto3.client("codepipeline")
    REST_API_ID = os.environ["REST_API_ID"]
    STAGE_NAME = os.environ["STAGE_NAME"]
    client.create_deployment(restApiId=REST_API_ID, stageName=STAGE_NAME)
    response = pipeline.put_job_success_result(jobId=event["CodePipeline.job"]["id"])
    return response
