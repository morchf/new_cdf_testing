import json
import logging
import signal
import boto3
import os
import uuid
import cfnresponse

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def send_response(
    event, context, response_status, response_data, physicalResourceId=None
):
    cfnresponse.send(event, context, response_status, response_data, physicalResourceId)


def createCerts(region_name):
    iot = boto3.client("iot", region_name=region_name)
    result = iot.create_keys_and_certificate(setAsActive=True)
    certarn = result.get("certificateArn")
    certpem = result["certificatePem"]
    certprivate = result["keyPair"]["PrivateKey"]
    policy_name = f'{os.environ["StackName"]}-{uuid.uuid4()}'
    iot.create_policy(
        policyName=policy_name,
        policyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["iot:Subscribe", "iot:Connect", "iot:Receive"],
                        "Resource": ["*"],
                    }
                ],
            }
        ),
    )
    iot.attach_policy(policyName=policy_name, target=certarn)
    return certpem, certprivate, policy_name


def storeCerts(region_name, certpem, certkey):
    ssm = boto3.client("ssm", region_name=region_name)
    ssm.put_parameter(
        Name=f'{os.environ["StackName"]}-cert.pem', Value=certpem, Type="SecureString"
    )
    ssm.put_parameter(
        Name=f'{os.environ["StackName"]}-key.key', Value=certkey, Type="SecureString"
    )


def createAndStoreCerts(region_name):
    certpem, certkey, policy_name = createCerts(region_name)
    storeCerts(region_name, certpem, certkey)
    return policy_name


def deleteCerts(region_name, policyName):
    ssm = boto3.client("ssm", region_name=region_name)
    iot = boto3.client("iot", region_name=region_name)

    ssm.delete_parameter(Name=f'{os.environ["StackName"]}-cert.pem')
    ssm.delete_parameter(Name=f'{os.environ["StackName"]}-key.key')

    certarn = iot.list_targets_for_policy(policyName=policyName)["targets"][0]
    iot.detach_policy(policyName=policyName, target=certarn)
    iot.delete_policy(policyName=policyName)

    iot.update_certificate(certificateId=certarn.split("/")[-1], newStatus="INACTIVE")
    iot.delete_certificate(certificateId=certarn.split("/")[-1], forceDelete=True)


def lambda_handler(event, context):
    try:
        if event["RequestType"] == "Create":
            policy_name = createAndStoreCerts(
                event["ResourceProperties"]["ServiceToken"].split(":")[3]
            )
            send_response(
                event,
                context,
                cfnresponse.SUCCESS,
                {"Message": "Resource creation successful"},
                policy_name,
            )
            return
        elif event["RequestType"] == "Delete":
            deleteCerts(
                event["ResourceProperties"]["ServiceToken"].split(":")[3],
                event["PhysicalResourceId"],
            )
            send_response(
                event,
                context,
                cfnresponse.SUCCESS,
                {"Message": "Resource deletion successful"},
            )
            return
    except Exception as e:
        send_response(
            event,
            context,
            cfnresponse.FAILED,
            {"Message": f"Failed to Create Custom Stored Certificates: {e}"},
        )
        return

    send_response(
        event,
        context,
        cfnresponse.SUCCESS,
        {"Message": "All other operations are passed through on this resource"},
    )


def timeout_handler(_signal, _frame):
    raise Exception("Time exceeded")


signal.signal(signal.SIGALRM, timeout_handler)
