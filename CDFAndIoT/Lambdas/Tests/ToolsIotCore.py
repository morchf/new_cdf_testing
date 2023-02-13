import requests
import json
import boto3
import uuid
import tempfile
import os
import time
import threading
import logging
from functools import wraps
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt

def log(msg, logger=None):
    if logger:
        logger.warning(msg)
    else:
        print(msg)

def retry(exceptions, total_tries=4, initial_wait=0.5, backoff_factor=2, logger=None):
    """Calling the decorated function applying an exponential backoff.

    Args:
        exceptions (Exception): Exception(s) that trigger a retry, can be a tuple
        total_tries (int, optional): Total tries. Defaults to 4.
        initial_wait (float, optional): Time to first retry. Defaults to 0.5.
        backoff_factor (int, optional): Backoff multiplier (e.g. value of 2 will double the delay each retry). Defaults to 2.
        logger ([type], optional): Logger to be used, if none specified print. Defaults to None.
    """
    def retry_decorator(f):
        @wraps(f)
        def func_with_retries(*args, **kwargs):
            _tries, _delay = total_tries + 1, initial_wait
            while _tries > 1:
                try:
                    log(f'{total_tries + 2 - _tries}. try:', logger)
                    return f(*args, **kwargs)
                except exceptions as e:
                    _tries -= 1
                    print_args = args if args else 'no args'
                    if _tries == 1:
                        msg = str(f'Function: {f.__name__}\n'
                                  f'Failed despite best efforts after {total_tries} tries.\n'
                                  f'args: {print_args}, kwargs: {kwargs}'
                        )
                        log(msg, logger)
                        raise
                    msg = str(f'Function: {f.__name__}\n'
                              f'Exception: {e}\n'
                              f'Retrying in {_delay} seconds!, args: {print_args}, kwargs: {kwargs}\n'
                    )
                    log(msg, logger)
                    time.sleep(_delay)
                    _delay *= backoff_factor
        return func_with_retries
    return retry_decorator

@retry(Exception)
def GetAwsRootCa():
    response = requests.request(method='GET', url="https://www.amazontrust.com/repository/AmazonRootCA1.pem")
    return response.text

def CreateCertForTopic(topic, region_name=None, mode='r'):
    try:
        certarn, certid, policy_name = None, None, None
        iot = boto3.client('iot') if not region_name else boto3.client('iot', region_name=region_name)
        result = iot.create_keys_and_certificate(setAsActive=True)
        certarn = result.get('certificateArn')
        certid = result.get('certificateId')
        certpem = result['certificatePem']
        certpublic = result['keyPair']['PublicKey']
        certprivate = result['keyPair']['PrivateKey']
        if certarn:
            policy_name = f'TestSubscribe-{uuid.uuid4()}'
            iot.create_policy(
                policyName=policy_name,
                policyDocument=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "iot:Subscribe",
                                "iot:Connect",
                                "iot:Publish",
                                "iot:Receive"
                            ],
                            "Resource": ["*"]
                        }
                    ]
                })
            )
            iot.attach_policy(policyName=policy_name, target=certarn)
        return {
            'policyName': policy_name,
            'certificateArn': certarn,
            'certificateId': certid,
            'certificatePem': certpem,
            'certificatePublicKey': certpublic,
            'certificatePrivateKey': certprivate
        }
    except:
        DeleteCertForTopic(policy_name, certarn, certid, region_name)
        return None

@retry(Exception)
def DeleteCertForTopic(policyName, certificateArn, certificateId, region_name='us-east-1'):
    error = False

    iot = boto3.client('iot') if not region_name else boto3.client('iot', region_name=region_name)
    try:
        result = iot.detach_policy(policyName=policyName, target=certificateArn)
    except Exception as e:
        error = f"Could not detach Policy: {e}"

    try:
        result = iot.delete_policy(policyName=policyName)
    except Exception as e:
        error = f"Could not delete Policy: {e}"

    try:
        result = iot.update_certificate(certificateId=certificateId, newStatus="INACTIVE")
    except Exception as e:
        error = f"Could not deactivate Certificate: {e}"

    try:
        result = iot.delete_certificate(certificateId=certificateId, forceDelete=True)
    except Exception as e:
        error = f"Could not delete Certificate: {e}"
    
    if error:
        raise ValueError(error)

def VerifyTopic(topic, timeout=20):
    certs = CreateCertForTopic(topic)
    rootCa = GetAwsRootCa()

    result = False
    try:
        certfd, certpath = tempfile.mkstemp()
        with open(certpath, 'w') as f:
            f.write(certs['certificatePem'])
        keyfd, keypath = tempfile.mkstemp()
        with open(keypath, 'w') as f:
            f.write(certs['certificatePrivateKey'])
        cafd, capath = tempfile.mkstemp()
        with open(capath, 'w') as f:
            f.write(rootCa)

        publishedEvent = threading.Event()
        def on_message(topic, payload):
            publishedEvent.set()

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint="axxai1lkxmzlb-ats.iot.us-east-1.amazonaws.com",
            client_bootstrap=client_bootstrap,
            client_id=str(uuid.uuid4()).encode(),
            cert_filepath=certpath,
            pri_key_filepath=keypath,
            ca_filepath=capath,
            keep_alive_secs=6
        )
        connect_future = mqtt_connection.connect()
        connect_future.result()
        subscribe_future, packet_id = mqtt_connection.subscribe(topic=topic, callback=on_message, qos=mqtt.QoS.AT_LEAST_ONCE)
        subscribe_future.result()
        publishedEvent.wait(timeout=timeout)
        result = publishedEvent.is_set()
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()

        os.close(certfd)
        os.remove(certpath)
        os.close(keyfd)
        os.remove(keypath)
        os.close(cafd)
        os.remove(capath)
    except Exception as e:
        print(f"Failed to Connect {e}")
    finally:
        DeleteCertForTopic(certs['policyName'], certs['certificateArn'], certs['certificateId'])

    return result

if __name__ == "__main__":
    result = VerifyTopic(f"SimDevice0101/messages/json")
    print(f"Result for topic SimDevice0101/messages/json: {result}")
