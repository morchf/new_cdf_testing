import requests
import json
import boto3
import uuid
import os
import threading
import time
import logging
from multiprocessing import Pipe
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
from datetime import datetime
from pytz import timezone

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def GetAwsRootCa():
    response = requests.request(
        method="GET", url="https://www.amazontrust.com/repository/AmazonRootCA1.pem"
    )
    return response.text


def CertsExist():
    return (
        os.path.isfile("/tmp/cert.pem")
        and os.path.isfile("/tmp/key.key")
        and os.path.isfile("/tmp/rootca.pem")
    )


def DownloadCerts():
    parameter1 = f'{os.environ["StackName"]}-cert.pem'
    parameter2 = f'{os.environ["StackName"]}-key.key'
    response = boto3.client("ssm").get_parameters(
        Names=[parameter1, parameter2], WithDecryption=True
    )
    for i in response["Parameters"]:
        with open(f'/tmp/{i["Name"].split("-")[-1]}', "w") as f:
            f.write(i["Value"])

    with open("/tmp/rootca.pem", "w") as f:
        f.write(GetAwsRootCa())


headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}
iot_endpoint = boto3.client("iot").describe_endpoint(endpointType="iot:Data-ATS")[
    "endpointAddress"
]
if not CertsExist():
    DownloadCerts()


def SubscribeIotCore(topic, wait_condition, callback=None):
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=iot_endpoint,
        client_bootstrap=client_bootstrap,
        client_id=str(uuid.uuid4()).encode(),
        cert_filepath="/tmp/cert.pem",
        pri_key_filepath="/tmp/key.key",
        ca_filename="/tmp/rootca.pem",
        keep_alive_secs=6,
    )
    connect_future = mqtt_connection.connect()
    connect_future.result()
    subscribe_future, _ = mqtt_connection.subscribe(
        topic=topic, callback=callback, qos=mqtt.QoS.AT_LEAST_ONCE
    )
    subscribe_future.result()

    wait_condition()

    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()


def ListenToSingleTopicMessage(topic, timeout=20):
    data = None
    try:
        pipe_out, pipe_in = Pipe()
        publishedEvent = threading.Event()

        def on_message(topic, payload):
            try:
                pipe_in.send({"topic": topic, "payload": payload})
                publishedEvent.set()
            except Exception as e:
                print(e)
                LOGGER.info(str(e))

        def wait_condition():
            publishedEvent.wait(timeout=timeout)

        SubscribeIotCore(topic, wait_condition, on_message)

        pipe_in.close()

        data = pipe_out.recv()
    except Exception as e:
        LOGGER.info(f"Failed to Connect {e}")
        return {"errorMessage": str(e)}

    return data


def getDataSetId(name):
    qs = boto3.client("quicksight")
    response = qs.list_data_sets(
        AwsAccountId=boto3.client("sts").get_caller_identity().get("Account")
    )
    for i in response["DataSetSummaries"]:
        if i["Name"] == name:
            return i["DataSetId"]


def getDashboardId(name):
    qs = boto3.client("quicksight")
    response = qs.list_dashboards(
        AwsAccountId=boto3.client("sts").get_caller_identity().get("Account")
    )
    for i in response["DashboardSummaryList"]:
        if i["Name"] == name:
            return i["DashboardId"]


def sendRequest(method, url, creds, headers={}, data={}):
    request = AWSRequest(method=method, url=url, data={}, headers=headers)

    SigV4Auth(creds, "execute-api", "us-east-1").add_auth(request)

    return URLLib3Session().send(request.prepare())


def getDevice(searchedType, searchedInput):
    creds = boto3.Session().get_credentials()
    deviceList = json.loads(
        sendRequest(
            "GET",
            f"{os.environ['CDFEndpoint']}"
            f"/search?type=communicator&eq={searchedType}%3A{searchedInput}",
            creds,
            headers,
        ).content
    )["results"]
    LOGGER.info(f"{deviceList}")
    return deviceList


def lambda_handler(event, context):
    gttSerial = event["queryStringParameters"].get("gttSerialNumber")
    serial = event["queryStringParameters"].get("serialNumber")
    LOGGER.info(f"GttSerial: {gttSerial}, Serial: {serial}")

    # Search device serial/gttSerial number in the Asset Lib
    if serial in ["[ALL]", "All"] and gttSerial in ["[ALL]", "All"]:
        deviceList = []
    elif serial not in ["[ALL]", "All"]:
        deviceList = getDevice("serial", serial)
    else:
        deviceList = getDevice("gttSerial", gttSerial)

    s3 = boto3.client("s3")
    now = datetime.now(timezone("US/Central")).strftime("%Y-%m-%d %H:%M:%S %Z")
    if deviceList == []:
        # Update vehicleResults.csv in S3
        s3.put_object(
            Bucket=os.environ["S3DataVizBucket"],
            Body="serialNumber,ignition,leftBlinker,rightBlinker,lightBar,disable,"
            "latitude,longitude,heading,speed,fixStatus,numberFixSatellites,"
            "timestamp,macAddress,imei,gttSerial,ip,now\n"
            f",,,,,,,,,,,,,,,,,{now}",
            Key="VISUALIZATIONS/VEHILCETROUBLESHOOTINGREALTIME/vehicleResults.csv",
        )
    else:
        LOGGER.info(f"{deviceList}")
        device = deviceList[0]["attributes"]
        deviceId = deviceList[0]["attributes"]["serial"]

        # Get IoT message
        topic = f"{deviceId}/messages/json"
        LOGGER.info(f"Listening to Topic: {topic}")
        data = ListenToSingleTopicMessage(topic, timeout=4)
        try:
            data = json.loads(data["payload"])
            key = list(data.keys())[0]
            data = data[key]
            gpios = [int(b) for b in "{:08b}".format(data.get("atp.gpi"))]
            ignition = gpios[7]
            leftBlinker = gpios[6]
            rightBlinker = gpios[5]
            lightBar = gpios[4]
            disable = gpios[3]
        except Exception as e:
            LOGGER.info(f"Error in listening to Topic: {e}")
            data, key = {}, ""
            ignition, leftBlinker, rightBlinker, lightBar, disable = "", "", "", "", ""

        # Update vehicleResults.csv in S3
        s3.put_object(
            Bucket=os.environ["S3DataVizBucket"],
            Body="serialNumber,ignition,leftBlinker,rightBlinker,lightBar,disable,"
            "latitude,longitude,heading,speed,fixStatus,numberFixSatellites,"
            "timestamp,macAddress,imei,gttSerial,ip,now\n"
            f"{device.get('serial', serial)},{ignition},{leftBlinker},"
            f"{rightBlinker},{lightBar},{disable},{data.get('atp.glat', '')},"
            f"{data.get('atp.glon', '')},{data.get('atp.ghed', '')},"
            f"{data.get('atp.gspd', '')},{data.get('atp.gstt', '')},"
            f"{data.get('atp.gsat', '')},{key},"
            f"{device.get('addressMAC', '')},{device.get('IMEI', '')},"
            f"{device.get('gttSerial', '')},{device.get('addressLAN', '')},{now}",
            Key="VISUALIZATIONS/VEHILCETROUBLESHOOTINGREALTIME/vehicleResults.csv",
        )

    # Refresh Quicksight
    LOGGER.info("Refreshing quicksight Dashboard")
    qs = boto3.client("quicksight")
    datasetId = getDataSetId(os.environ["DatasetName"])
    AwsAccountId = boto3.client("sts").get_caller_identity().get("Account")
    response = qs.create_ingestion(
        DataSetId=datasetId, IngestionId=str(uuid.uuid4()), AwsAccountId=AwsAccountId
    )
    ingestion_id = response["IngestionId"]

    for i in range(10):
        response = qs.describe_ingestion(
            DataSetId=datasetId, IngestionId=ingestion_id, AwsAccountId=AwsAccountId
        )
        if response["Ingestion"]["IngestionStatus"] in (
            "INITIALIZED",
            "QUEUED",
            "RUNNING",
        ):
            time.sleep(1)
        elif response["Ingestion"]["IngestionStatus"] == "COMPLETED":
            print("Refresh Successful - Redirecting ")
            break
        else:
            print("Refresh Failed!")

    # Redirect to the updated dashboard
    return_val = {
        "statusCode": 302,
        "headers": {
            "Content-Type": "application/json",
            "Location": "https://us-east-1.quicksight.aws.amazon.com/sn/"
            f"dashboards/{getDashboardId(os.environ['DashboardName'])}#"
            "p.gttSerialNumber="
            f"{event['queryStringParameters'].get('gttSerialNumber')}&"
            "p.serialNumber="
            f"{event['queryStringParameters'].get('serialNumber')}",
        },
    }

    return return_val
