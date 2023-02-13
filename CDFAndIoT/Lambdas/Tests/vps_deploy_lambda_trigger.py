import json
import datetime
import boto3
 
def invoke_gttvpsdeploy(customerName, region_name=None):
    lambda_client = boto3.client("lambda") if region_name is None else boto3.client("lambda", region_name=region_name)

    response = lambda_client.invoke(
        FunctionName='gttvpsdeploy',
        InvocationType='RequestResponse',
        Payload=json.dumps({'customerName': customerName})
    )

    return response['Payload'].read().decode('utf-8') == 'null'
    