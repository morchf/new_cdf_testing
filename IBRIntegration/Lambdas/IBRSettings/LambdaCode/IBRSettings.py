import json
import os
from boto3 import client
from boto3 import Session
from os import environ
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth


client = client("iot-data", environ["AWS_REGION"])
url = environ["CDF_URL"]

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

settings = {
    "Priority": "High",
    "GPIO_POWERCBL": "CONNECTOR_INPUT",
    "GPIO_1": "SATA_GPIO_1",
    "GPIO_2": "SATA_GPIO_2",
    "GPIO_3": "SATA_GPIO_3",
    "GPIO_4": "SATA_GPIO_4",
    "GPIO_IGNITION": "SATA_IGNITION_SENSE",
    "gpioPowercblPolarity": "Standard",
    "gpio1Polarity": "Standard",
    "gpio2Polarity": "Standard",
    "gpio3Polarity": "Standard",
    "gpio4Polarity": "Standard",
    "gpioIgnitionPolarity": "Standard",
}


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )  # noqa: E501
    return URLLib3Session().send(request.prepare()).content


def lambda_handler(event, context):
    print(event)
    pub_topic = event.get("topic")

    if not pub_topic:
        raise Exception("No topic in event data")

    # get SN from topic
    # Topic is always SN/messages/json where SN is the serial number of the modem
    split_topic = pub_topic.split("/")
    client_id = split_topic[3]
    model = split_topic[2]
    # get data from the CDF
    comData = CDF_get_device(client_id)
    cdf_vehicle_id = comData["devices"]["in"]["installedat"][0]
    vehicleData = CDF_get_device(cdf_vehicle_id).get("attributes")
    comAtt = comData.get("attributes")
    print(f"comData = {comData}")
    print(f"vehicleData = {vehicleData}")

    settings["Priority"] = vehicleData.get("priority", settings["Priority"])
    settings["GPIO_POWERCBL"] = comAtt.get("gpioPowercbl", settings["GPIO_POWERCBL"])
    settings["GPIO_1"] = comAtt.get("gpio1", settings["GPIO_1"])
    settings["GPIO_2"] = comAtt.get("gpio2", settings["GPIO_2"])
    settings["GPIO_3"] = comAtt.get("gpio3", settings["GPIO_3"])
    settings["GPIO_4"] = comAtt.get("gpio4", settings["GPIO_4"])
    settings["GPIO_IGNITION"] = comAtt.get("gpioIgnition", settings["GPIO_IGNITION"])
    settings["gpioPowercblPolarity"] = comAtt.get(
        "gpioPowercblPolarity", settings["gpioPowercblPolarity"]
    )
    settings["gpio1Polarity"] = comAtt.get("gpio1Polarity", settings["gpio1Polarity"])
    settings["gpio2Polarity"] = comAtt.get("gpio2Polarity", settings["gpio2Polarity"])
    settings["gpio3Polarity"] = comAtt.get("gpio3Polarity", settings["gpio3Polarity"])
    settings["gpio4Polarity"] = comAtt.get("gpio4Polarity", settings["gpio4Polarity"])
    settings["gpioIgnitionPolarity"] = comAtt.get(
        "gpioIgnitionPolarity", settings["gpioIgnitionPolarity"]
    )

    new_topic = f"CP/GTT/{model}/{client_id}/SETTINGS/RESP"

    # Send out new Topic to CMS associated with the client_id
    try:
        client.publish(topic=new_topic, qos=0, payload=json.dumps(settings))
        print(f"Published settings for {client_id} - {settings}")  # noqa: E501)
    except Exception as e:
        print(f"Unable to get settings for {client_id}: Error - {e}")


def CDF_get_device(device_id):
    device_id = device_id
    request_url = f"{url}/devices/{device_id}"
    # print(f"cache: pull_com_from_CDF request_url = {request_url}")
    requested_info = send_request(
        request_url, "GET", os.environ["AWS_REGION"], headers=headers
    )
    requested_info = json.loads(requested_info)
    # print(f"cache : pull_com_from_CDF requested_info = {requested_info}")
    return requested_info
