import boto3
import os
import json
import datetime

s3 = boto3.resource("s3")
states = boto3.client("stepfunctions")


def getDashboardId(name):
    qs = boto3.client("quicksight")
    response = qs.list_dashboards(
        AwsAccountId=boto3.client("sts").get_caller_identity().get("Account")
    )
    for i in response["DashboardSummaryList"]:
        if i["Name"] == name:
            return i["DashboardId"]


def lambda_handler(event, context):
    try:
        obj = s3.Object(
            os.environ["s3Bucket"],
            "VISUALIZATIONS/VEHICLETROUBLESHOOTING/stepFunctionResult.json",
        )
        results = json.loads(obj.get()["Body"].read())
        resultTime = datetime.datetime.strptime(
            results["resultTimestamp"], "%Y/%m/%d %H:%M:%S"
        )
        currentTime = datetime.datetime.now() - datetime.timedelta(minutes=30)
        if results["status"] == "SUCCESS" and resultTime < currentTime:
            states.start_execution(stateMachineArn=os.environ["stateMachineArn"])
    except Exception as e:
        print(e)
        states.start_execution(stateMachineArn=os.environ["stateMachineArn"])

    return {
        "statusCode": 200,
        "body": f"https://{os.environ['Region']}.quicksight.aws.amazon.com/sn/"
        f'dashboards/{getDashboardId(os.environ["DashboardName"])}',
    }
