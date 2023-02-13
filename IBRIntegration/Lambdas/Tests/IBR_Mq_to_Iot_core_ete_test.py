# flake8: noqa
# fmt: off
import requests
import json
import boto3
import uuid
import tempfile
import os
import sys
import time
import threading
from os import environ
import random
import ast
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt
#from boto3 import client

vehicle_id = b"\x17\x12"
vehicle_city_id = b"\x0c"
vehicle_class_bytes = b"\n"
global byte_data


IOT_ENDPOINT = environ["IOT_CORE_ENDPOINT"]
iot_client = boto3.client("iot-data", environ["AWS_REGION"])


def call_time():
    named_tuple = time.localtime()
    time_string = time.strftime(f"%m/%d/%Y %I:%M:%S %p", named_tuple)
    return time_string

def generate_data():
    data = json.dumps(
        {
        "fix": {
            "latitude": {
            "degree": 38,
            "minute": 0,
            "second": 41.00117999999213
            },
            "longitude": {
            "degree": -122,
            "minute": 1,
            "second": 31.837140000006908
            },
            "from_sentence": "GPGGA",
            "satellites": 8,
            "time": 165923,
            "lock": "True",
            "age": 0.0013411879999694063,
            "altitude_meters": 16,
            "ground_speed_knots": 0,
            "heading": 359.8,
            "accuracy": 3.5
        },
        "gpio": {
            "pwrIn": 0,
            "io1": 0,
            "io2": 0,
            "io3": 1,
            "io4": 1,
            "io5": 0
        },
        "topic": "CP/GTT/EVP/IBR900-600M/wa214700583962/STATE"
        }
    )
    return data

global body
body = generate_data()

def push_message():
    iot_client = boto3.client("iot-data", environ["AWS_REGION"])
    data = json.loads(generate_data())
    topic = data["topic"]
    iot_client.publish(topic=topic, qos=0, payload=json.dumps(data))
    time.sleep(2)

def GetAwsRootCa():
    response = requests.request(
        method="GET", url="https://www.amazontrust.com/repository/AmazonRootCA1.pem"
    )
    return response.text


def CreateCertForTopic(topic, region_name=None, mode="r"):
    try:
        certarn, certid, policy_name = None, None, None
        iot = (
            boto3.client("iot")
            if not region_name
            else boto3.client("iot", region_name=region_name)
        )
        result = iot.create_keys_and_certificate(setAsActive=True)
        certarn = result.get("certificateArn")
        certid = result.get("certificateId")
        certpem = result["certificatePem"]
        certpublic = result["keyPair"]["PublicKey"]
        certprivate = result["keyPair"]["PrivateKey"]
        if certarn:
            policy_name = f"TestIBR-{uuid.uuid4()}"
            iot.create_policy(
                policyName=policy_name,
                policyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "iot:Subscribe",
                                    "iot:Connect",
                                    "iot:Publish",
                                    "iot:Receive",
                                ],
                                "Resource": ["*"],
                            }
                        ],
                    }
                ),
            )
            iot.attach_policy(policyName=policy_name, target=certarn)
        return {
            "policyName": policy_name,
            "certificateArn": certarn,
            "certificateId": certid,
            "certificatePem": certpem,
            "certificatePublicKey": certpublic,
            "certificatePrivateKey": certprivate,
        }
    except Exception as e:
        print(f"Connection failure - {e}")
        DeleteCertForTopic(policy_name, certarn, certid, region_name)
        return None


def DeleteCertForTopic(
    policyName, certificateArn, certificateId, region_name="us-east-1"
):

    result = None
    error = False

    iot = (
        boto3.client("iot")
        if not region_name
        else boto3.client("iot", region_name=region_name)
    )
    try:
        result = iot.detach_policy(policyName=policyName, target=certificateArn)
    except Exception as e:
        error = f"Could not detach Policy: {e}"

    try:
        result = iot.delete_policy(policyName=policyName)
    except Exception as e:
        error = f"Could not delete Policy: {e}"

    try:
        result = iot.update_certificate(
            certificateId=certificateId, newStatus="INACTIVE"
        )
    except Exception as e:
        error = f"Could not deactivate Certificate: {e}"

    try:
        result = iot.delete_certificate(certificateId=certificateId, forceDelete=True)
    except Exception as e:
        error = f"Could not delete Certificate: {e}"

    if error:
        raise ValueError(error)

    return result

def VerifyTopic(topic, timeout=20):
    certs = CreateCertForTopic(topic)
    rootCa = GetAwsRootCa()

    result = False
    try:
        certfd, certpath = tempfile.mkstemp()
        with open(certpath, "w") as f:
            f.write(certs["certificatePem"])
        keyfd, keypath = tempfile.mkstemp()
        with open(keypath, "w") as f:
            f.write(certs["certificatePrivateKey"])
        cafd, capath = tempfile.mkstemp()
        with open(capath, "w") as f:
            f.write(rootCa)

        publishedEvent = threading.Event()

        def on_message(topic, payload): 
            global byte_data
            byte_data = payload
            print("Received message from topic '{}': {}".format(topic, payload))
            publishedEvent.set()

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=IOT_ENDPOINT,
            client_bootstrap=client_bootstrap,
            client_id=str(uuid.uuid4()).encode(),
            cert_filepath=certpath,
            pri_key_filepath=keypath,
            ca_filepath=capath,
            keep_alive_secs=6,
        )
        connect_future = mqtt_connection.connect()
        connect_future.result()
        subscribe_future, packet_id = mqtt_connection.subscribe(
            topic=topic, callback=on_message, qos=mqtt.QoS.AT_LEAST_ONCE
        )
        push_message()
        result = subscribe_future.result()
        publishedEvent.wait(timeout=timeout)
        publishedEvent.is_set()
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()

        os.close(certfd)
        os.remove(certpath)
        os.close(keyfd)
        os.remove(keypath)
        os.close(cafd)
        os.remove(capath)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"Failed to Connect  {e} {exc_type} {fname} {exc_tb.tb_lineno}...")
    finally:
        DeleteCertForTopic(
            certs["policyName"], certs["certificateArn"], certs["certificateId"]
        )

    return result


def convert_lat_lon_to_minutes_degrees(lat, lon):
    return_lat = to_min_degrees(lat)
    return_lon = to_min_degrees(lon)
    return return_lat, return_lon


def to_min_degrees(data):
    data = float(data)
    ddd = int(data)
    mmmmmm = float(data - float(ddd)) * 60
    data = (ddd * 1000000 + int(mmmmmm * 10000)) / 1000000
    new_string = hex(int(data * 1000000))
    int_data = int(new_string, 16)
    return_data = int_data.to_bytes(4, byteorder="little", signed=True)
    return return_data


def convert_speed(speed):
    speed = int(speed)
    new_speed = int(speed * 1000 * 5 / 3600)
    return new_speed.to_bytes(1, byteorder="little", signed=False)


def convert_heading(heading):
    heading = int(heading)
    new_heading = int(heading / 2 + 0.5)
    return new_heading.to_bytes(1, byteorder="little", signed=False)

def dms_to_min_degrees(degrees, minutes, seconds):
    #if degrees are negative, reverse the equasion for calculation
    if (degrees < 1):
        return ( (degrees*-1) + ((minutes / 60) + (round(seconds,6) / 3600))) * -1
    return degrees + (minutes / 60) + (round(seconds,6) / 3600)

"""Checking vehicle data from lambda to iot core"""


def test_check_iot_core():
    VerifyTopic(f"GTT/+/SVR/EVP/2100/WA214700583962/RTRADIO/#")
    json_body = ast.literal_eval(body)
    #raw_message_id = json_body["messageId"]
    raw_lat_degree = json_body["fix"]["latitude"]["degree"]
    raw_lat_minute = json_body["fix"]["latitude"]["minute"]
    raw_lat_second = json_body["fix"]["latitude"]["second"]
    raw_long_degree = json_body["fix"]["longitude"]["degree"]
    raw_long_minute = json_body["fix"]["longitude"]["minute"]
    raw_long_second = json_body["fix"]["longitude"]["second"]
    raw_heading = json_body["fix"]["heading"]
    raw_ground_speed_knots = json_body["fix"]["ground_speed_knots"]

    lat = dms_to_min_degrees(raw_lat_degree, raw_lat_minute, raw_lat_second)
    lon = dms_to_min_degrees(raw_long_degree, raw_long_minute, raw_long_second)
    lat = round(float(lat),6)
    lon = round(float(lon),6)


    bytes_lat, bytes_long = convert_lat_lon_to_minutes_degrees(lat, lon)
    bytes_speed = convert_speed(raw_ground_speed_knots)
    bytes_direction = convert_heading(raw_heading)

    sleepCount = 0
    while byte_data is None and sleepCount < 5:
        time.sleep(3)
        sleepCount = sleepCount +1
    
    print(f"bytes_lat = {bytes_lat} vs {byte_data[8:12]}")
    print(f"bytes_long = {bytes_long} vs {byte_data[12:16]}")
    print(f"bytes_speed = {bytes_speed} vs {byte_data[16:17]}")
    print(f"bytes_direction = {bytes_direction} vs { byte_data[17:18]}")
    print(f"vehicle_id = {vehicle_id} vs {byte_data[24:26]}")
    print(f"vehicle_city_id = {vehicle_city_id} vs {byte_data[26:27]}")
    print(f"vehicle_class_bytes = {vehicle_class_bytes} vs {byte_data[28:29]}")


    assert bytes_lat == byte_data[8:12], "Latitude is not matching"
    assert bytes_long == byte_data[12:16], "Longitude is not matching"
    assert bytes_speed == byte_data[16:17], "Vehicle speed is not matching"
    assert bytes_direction == byte_data[17:18], "Vehicle direction is not matching"
    assert vehicle_id == byte_data[24:26], "Vehicle id is not matching"
    assert vehicle_city_id == byte_data[26:27], "Vehicle city id is not matching"
    assert vehicle_class_bytes == byte_data[28:29], "Vehicle class is not matching"
