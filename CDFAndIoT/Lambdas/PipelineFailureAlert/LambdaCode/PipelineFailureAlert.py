import urllib3
import json
import os
import boto3

http = urllib3.PoolManager()


def lambda_handler(event, context):
    url = os.environ["TEAMS_URL"]
    env = os.environ["ENVIRONMENT"]
    event_message = event["Records"][0]["Sns"]["Message"]
    message_dict = json.loads(event_message)
    pipeline_name = message_dict["detail"]["pipeline"]
    pipeline_status = message_dict["detail"]["state"]
    client = boto3.client("codepipeline")
    response = client.get_pipeline(name=pipeline_name)
    branch_name = response["pipeline"]["stages"][0]["actions"][0]["configuration"][
        "BranchName"
    ]
    print(pipeline_name)
    msg = {
        "text": f"""\r\n
        This is to notify you that Pipeline: {pipeline_name} has: {pipeline_status}. \r\n
        Please check the {pipeline_name} pipeline in {env} environment and BranchName is {branch_name}"""
    }
    encoded_msg = json.dumps(msg).encode("utf-8")
    resp = http.request("POST", url, body=encoded_msg)
    print({"message": pipeline_name, "status_code": resp.status, "response": resp.data})
