import json
import os
import boto3
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth

# Create client here so that it will stay 'warm' between invocations saving execution time
client = boto3.client("iot-data", os.environ["AWS_REGION"])

headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}
base_url = os.environ["CDF_URL"]


def sendRequest(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=params,
        headers=headers,
    )
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    return URLLib3Session().send(request.prepare()).content


def lambda_handler(event, context):
    resp = False
    att_str = '{"attributes":{'
    orig_len = len(att_str)
    att_end = "}}"

    time = list(event.keys())[0]
    if not time:
        raise Exception("No timestamp in event")

    data = event.get(time)
    if not data:
        raise Exception("No data in event")

    # Get modem serial number
    # Sample topic: N684570206021035/messages/json
    SN = event.get("topic")

    if not SN:
        raise Exception("No topic in event")

    SN = SN.split("/")[0]

    # Assemble communicator URL
    url = f"{base_url}/devices/{SN.lower()}"

    code = sendRequest(url, "GET", os.environ["AWS_REGION"], headers=headers)
    # print(code)

    dataCommunicator = json.loads(code)

    # use communicator data to get vehicle data where the data is stored
    devices = dataCommunicator.get("devices")
    print(devices)
    if not devices:
        raise Exception("No vehicle associated with communicator")

    if devices:
        device_in = devices.get("in")

    # sometimes device data has out sometimes it doesn't; handle both cases
    if device_in:
        installedat = device_in.get("installedat")
    else:
        installedat = devices.get("installedat")

    vehicle = installedat[0]

    # Store data in local vars, set to "No Data" if key not found
    # Note: no message has all the data saved here
    lat = data.get("atp.glat")  # Current latitude
    lon = data.get("atp.glon")  # Current longitude
    hdg = data.get("atp.ghed")  # Current heading
    spd = data.get("atp.gspd")  # Current speed kmph
    stt = data.get("atp.gstt")  # GPS fix status (0 = no fix, 1 = fix)
    sat = data.get("atp.gsat")  # Number of satellites at time of message
    gpi = data.get("atp.gpi")  # GPIO state - bit masked

    if stt:
        att_str += f'"fixStatus":{stt},'

    if sat:
        att_str += f'"numFixSat":{sat},'

    if lat:
        att_str += f'"lat":{lat},'

    if lon:
        att_str += f'"long":{lon},'

    if hdg:
        att_str += f'"heading":{hdg},'

    if spd:
        att_str += f'"speed":{spd},'

    if gpi:
        att_str += f'"auxiliaryIo":{gpi},'
        att_str += f'"lastGPIOMsgTimestamp":"{time}",'

    if stt or sat or lat or lon or hdg or spd:
        att_str += f'"lastGPSMsgTimestamp":"{time}",'

    # only PATCH if data to patch
    if len(att_str) > orig_len:
        # remove comma from end of string
        att_str = att_str.rstrip(",") + att_end
        print(att_str)

        url = f"{base_url}/devices/{vehicle.lower()}"
        resp = sendRequest(
            url, "PATCH", os.environ["AWS_REGION"], params=att_str, headers=headers
        )
        print(resp)

    return resp
