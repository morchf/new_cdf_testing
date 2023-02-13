import boto3
import cfnresponse

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("codeBuildDeploy")


def lambda_handler(event, context):
    """[summary]
    Insert data to the dynamoDB codeBuildDeploy Table
    Args:
        event ([json]): [add customer name , docker image,
         server region, server properties
        which includes security group and subnet id ]
    """
    try:
        table.put_item(
            Item={
                "customerName": event["ResourceProperties"]["customerName"],
                "dockerImage": event["ResourceProperties"]["dockerImage"],
                "serverProperties": {
                    "securityGroup": event["ResourceProperties"]["sgrpList"],
                    "subnetID": event["ResourceProperties"]["subnetID"],
                },
                "serverRegion": event["ResourceProperties"]["serverRegion"],
            }
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
