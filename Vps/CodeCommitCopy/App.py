from boto3.dynamodb.conditions import Key
import boto3
import os

import cfnresponse

repo_name = os.environ["REPONAME"]
mac_code = os.environ["MACCODE"]
client = boto3.client("codecommit")
dyanamoDBtable = "globalMacVps"


def lambda_handler(event, context):
    """[summary]
    Creates the starting record in the globalmacVPS and adds the
     files to gttvpsdeployment repositories
    Args:
        event ([type]): [description]
        context ([type]): [description]
    """
    try:
        try:
            commitID = boto3.client("codecommit").get_branch(
                repositoryName=repo_name, branchName="master"
            )["branch"]["commitId"]
        except Exception:
            commitID = None
        for item in [
            f
            for f in os.listdir(os.curdir)
            if os.path.isfile(f)
            and (".yml" in f or ".py" in f or ".jinja" in f)
            and ("App.py" not in f)
            and ("cfnresponse.py" not in f)
        ]:
            if not commitID:
                try:
                    response = client.put_file(
                        repositoryName=repo_name,
                        branchName="master",
                        fileContent=open(item, "r").read().encode(),
                        filePath=item,
                    )
                    commitID = response["commitId"]
                except Exception:
                    pass
            else:
                try:
                    response = client.put_file(
                        repositoryName=repo_name,
                        branchName="master",
                        fileContent=open(item, "r").read().encode(),
                        filePath=item,
                        parentCommitId=commitID,
                    )
                    commitID = response["commitId"]
                except Exception:
                    pass
        if (
            boto3.resource("dynamodb")
            .Table(dyanamoDBtable)
            .query(KeyConditionExpression=Key("primaryKey").eq(11111))["Count"]
            == 0
        ):
            boto3.client("dynamodb").put_item(
                TableName=dyanamoDBtable,
                Item={
                    "primaryKey": {"N": "11111"},
                    "macCode": {"N": str(int(mac_code.replace(":", ""), 16))},
                    "VPS": {"S": "V764MH0000"},
                },
            )
        responseData = {}
        responseData["Data"] = "SUCCESS"
        cfnresponse.send(
            event,
            context,
            cfnresponse.SUCCESS,
            responseData,
            "CustomResourcePhysicalID",
        )
    except Exception:
        responseData = {}
        responseData["Data"] = "ERROR"
        cfnresponse.send(
            event, context, cfnresponse.FAILED, responseData, "CustomResourcePhysicalID"
        )
