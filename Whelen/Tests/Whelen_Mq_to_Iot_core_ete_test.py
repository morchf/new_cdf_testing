# flake8: noqa
# fmt: off
import requests
import json
import boto3
import uuid
import tempfile
import os
import time
import threading
import stomp
import random
import ssl
import ast
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt


vehicle_id = b"\x8f\x19"
vehicle_city_id = b"\xe0"
vehicle_class_bytes = b"\x01"


def call_time():
    named_tuple = time.localtime()
    time_string = time.strftime(f"%m/%d/%Y %I:%M:%S %p", named_tuple)
    return time_string


def generate_data():
    data = json.dumps(
        {
            "messageId": str(uuid.uuid4()),
            "dateTime": call_time(),
            "gps": {
                "direction": f"{random.randint(0,360)}",
                "speed": f"{random.randint(1,160)}",
                "latitude": "{:.6f}".format(random.uniform(-90, 90)),
                "longitude": "{:.6f}".format(random.uniform(-180, 180)),
            },
            "turnSignal": random.choice(["Left", "Right", "None", "Both"]),
            "enable": "True",
            "disable": "False",
        }
    )
    return data


def push_message():
    user = "gtt"
    password = os.environ["MQ_PASS"]
    host = "b-acb7b446-25d1-4fa2-af93-dbc96c14a2e6-1.mq.us-east-1.amazonaws.com"
    port = 61614
    persistent = "false"
    reconnect_attempt = 0
    max_attempt = 10

    conn = stomp.Connection([(host, port)])
    conn.set_ssl(for_hosts=[(host, port)], ssl_version=ssl.PROTOCOL_TLS)
    while reconnect_attempt <= max_attempt:
        try: 
            conn.connect(login=user, passcode=password, wait=True)
            break
        except Exception as e:
            print(f"Connection Error: {e}")
            reconnect_attempt += 1

    destination = f"WHELEN.Whelen_Load_Com1.GTT.SCP.RTVEHDATA"
    global body
    body = generate_data()
    print('\nGenerated Data ---------------->', body)

    conn.send(destination, body, persistent)
    time.sleep(1)

    conn.disconnect()


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
            policy_name = f"TestWhelen-{uuid.uuid4()}"
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
    except:
        DeleteCertForTopic(policy_name, certarn, certid, region_name)
        return None


def DeleteCertForTopic(
    policyName, certificateArn, certificateId, region_name="us-east-1"
):
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
            endpoint="a1gvce2632u6tc-ats.iot.us-east-1.amazonaws.com",
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
        print(f"Failed to Connect {e}")
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


"""Checking vehicle data from lambda to iot core"""


def test_check_iot_core():
    VerifyTopic(f"GTT/whelen_load_agency1/SVR/EVP/2100/whelenCom001/RTRADIO/#")
    json_body = ast.literal_eval(body)
    raw_message_id = json_body["messageId"]
    raw_lat = json_body["gps"]["latitude"]
    raw_long = json_body["gps"]["longitude"]
    raw_speed = json_body["gps"]["speed"]
    raw_direction = json_body["gps"]["direction"]

    bytes_lat, bytes_long = convert_lat_lon_to_minutes_degrees(raw_lat, raw_long)
    bytes_speed = convert_speed(raw_speed)
    bytes_direction = convert_heading(raw_direction)

    assert bytes_lat == byte_data[8:12], "Latitude is not matching"
    assert bytes_long == byte_data[12:16], "Longitude is not matching"
    assert bytes_speed == byte_data[16:17], "Vehicle speed is not matching"
    assert bytes_direction == byte_data[17:18], "Vehicle direction is not matching"
    assert vehicle_id == byte_data[24:26], "Vehicle id is not matching"
    assert vehicle_city_id == byte_data[26:27], "Vehicle city id is not matching"
    assert vehicle_class_bytes == byte_data[28:29], "Vehicle class is not matching"

    time.sleep(65)

    s3 = boto3.resource('s3', region_name='us-east-1')
    s3Bucket = s3.Bucket('rt-radio-message')
    timePrefix = time.strftime(f"%Y/%m/%d/%H/", time.gmtime())
    s3BucketPrefix = f"Whelen/incoming_messages/{timePrefix}"

    dataBlob = s3Bucket.objects.filter(Prefix=s3BucketPrefix)
    
    for data in dataBlob:
        msg = data.get()['Body'].read().decode('utf-8')
        msg = msg[: -1]
        msg = json.loads(msg)
        
        if msg['messageId'] == raw_message_id:
            global s3_data
            s3_data = msg
            break
        
    print('Retrieved s3 data for checking --------->', s3_data)
    assert s3_data['gps'] == json_body['gps']
    assert s3_data['turnSignal'] == json_body['turnSignal']
    assert s3_data['enable'] == json_body['enable']
    assert s3_data['disable'] == json_body['disable']
    assert s3_data['topic'] == 'Whelen_Load_Com1'
