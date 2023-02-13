import argparse
import io
import math
import time
from pathlib import Path
from zipfile import ZipFile

import boto3
import requests
from boto3.dynamodb.conditions import Attr

#######################################################################################
PADDING = b"\x20"

IOTMQTTCOMMCFG_LENGTH = 267
IOTMQTTCOMMCFG_HEADER = b"\x00\x00\x00\x00\x02\x00\x00\x00"
IOTMQTTCOMMCFG_FOOTER = b"\x00\xB3\x22\x00\x00"

CERTIFICATEFILE_LENGTH = 4096
ROOTCA_HEADER = b"\x00"
CA_HEADER = b"\x01"
DEVICECERT_HEADER = b"\x02"
DEVICEKEY_HEADER = b"\x03"
########################################################################################
parser = argparse.ArgumentParser()
parser.add_argument(
    "--customerName",
    required=True,
    help="Customer name that should be referenced in codebuilddeploy dynamodb table",
)
args = parser.parse_args()
dynamoDBregion = "us-east-1"
dynamoDBtable = "globalMacVps"
dynamoResource = boto3.resource("dynamodb", region_name="us-east-1").Table(
    "codeBuildDeploy"
)

r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
response_json = r.json()
ec2_region = response_json.get("region")
instance_id = response_json.get("instanceId")
ec2 = boto3.resource("ec2", region_name=ec2_region)
instance = ec2.Instance(instance_id)
tags = instance.tags
agencyName = [tag.get("Value") for tag in tags if tag.get("Key") == "AGENCY"][0]
regionName = [tag.get("Value") for tag in tags if tag.get("Key") == "REGION"][0]

# The base url is provided by the devops team to fetch the zipfile contianing
#  all the certificates
S3Bucket = (
    boto3.resource("dynamodb", region_name="us-east-1")
    .Table("codeBuildDeploy")
    .scan(FilterExpression=Attr("customerName").eq("GTT"))["Items"]
)[0]["S3CertBucket"]

certificates = None
try:
    print(
        f"{regionName.upper()}/AGENCIES/{agencyName.upper()}/DEVICES/{agencyName.upper()}_VPS/filename.zip"
    )
    certificates = (
        boto3.client("s3")
        .get_object(
            Bucket=S3Bucket,
            Key=f"{regionName.upper()}/AGENCIES/{agencyName.upper()}/DEVICES/{agencyName.upper()}_VPS/filename.zip",
        )["Body"]
        .read()
    )
except Exception as e:
    print(f"Failed to read Agency Certificates: {e}")
    raise e
########################################################################################


def retGPS(val):
    """[Returns hexadecimal string]
    Arguments:
        val {[float]} -- [The decimal part could be either latitude or longitude]
    Returns:
        [string] -- [hexadecimal string]
    """
    ints = math.trunc(val)
    deci = abs(math.modf(val)[0]) * 60 / 100
    if ints > 0:
        retVal = (ints + deci) * 1000000
    elif ints < 0:
        retVal = (ints - deci) * 1000000
    elif ints == 0:
        if val < 0:
            retVal = -1 * deci * 1000000
        else:
            retVal = deci * 1000000
    if retVal > 0:
        hxcode = format(int(retVal), "03x").zfill(8)
    else:
        hxcode = format(int(retVal) & (2**32 - 1), "03x").zfill(8)
    return "".join(
        [hxcode[0:8][i : i + 2] for i in range(0, len(hxcode[0:8]), 2)][::-1]
    )


def WriteGpsCfgs(lat, lang, intersectionName, deviceName):
    """[updates the intersection information to the respective efs dockers]
    Arguments:
        lat {[float]} -- [latitude]
        lang {[float]} -- [longitude]
        intersectionName {[float]} -- [intersection name of the dockers]
        primarKey {[int]} -- [primarkey of the VPS device in the
         dynamodb table i.e, globalMacVps]
        deviceName {[string]} -- [VPS serial number]
    Keyword Arguments:
        dynamoRegion {[string]} -- [Dynamodb table region "us-east-1"]
         (default: {dynamoDBregion})
        dynamoTable {[string]} -- [Dyanmodb table name "globalMacVps"]
         (default: {dynamoDBtable})
    """
    try:
        bts = bytes(
            [
                int((retGPS(lat) + retGPS(lang))[0:16][i : i + 2], 16)
                for i in range(0, len((retGPS(lat) + retGPS(lang))[0:16]), 2)
            ]
        )
        Path("/efs/" + deviceName + "/gps_cfgs/GpsLocation").write_bytes(bts)
        Path("/efs/" + deviceName + "/misc_cfgs/Unit").write_text(
            "\0".join(list(intersectionName + " " * (40 - len(intersectionName[:40]))))
            + ("\0") * 36
        )
        Path("/efs/" + deviceName + "/gps_cfgs/GeoPointV1").touch()
        Path("/efs/" + deviceName + "/gps_cfgs/GpsFilter").write_text(
            "\x00" * 67 + "\x02" + "\x00" * 4
        )
    except Exception as e:
        print(f"Failed to write GPS configurations to Intersection {deviceName}: '{e}'")
        raise e


def GetCa(certificate):
    if type(certificate) == str:
        certificate = str.encode(certificate, "UTF-8")

    return (
        CA_HEADER
        + certificate
        + b"\x00"
        + (
            PADDING
            * (1 + CERTIFICATEFILE_LENGTH - len(CA_HEADER) - len(certificate) - 1)
        )
    )


def GetDeviceCert(certificate):
    if type(certificate) == str:
        certificate = str.encode(certificate, "UTF-8")

    return (
        DEVICECERT_HEADER
        + certificate
        + b"\x00"
        + (
            PADDING
            * (
                1
                + CERTIFICATEFILE_LENGTH
                - len(DEVICECERT_HEADER)
                - len(certificate)
                - 1
            )
        )
    )


def GetDeviceKey(certificate):
    if type(certificate) == str:
        certificate = str.encode(certificate, "UTF-8")

    return (
        DEVICEKEY_HEADER
        + certificate
        + b"\x00"
        + (
            PADDING
            * (
                1
                + CERTIFICATEFILE_LENGTH
                - len(DEVICEKEY_HEADER)
                - len(certificate)
                - 1
            )
        )
    )


def GetRootCa(certificate):
    if type(certificate) == str:
        certificate = str.encode(certificate, "UTF-8")

    return (
        ROOTCA_HEADER
        + certificate
        + b"\x00"
        + (
            PADDING
            * (1 + CERTIFICATEFILE_LENGTH - len(ROOTCA_HEADER) - len(certificate) - 1)
        )
    )


def GetIotEndpoint(region_name="us-east-1"):
    return boto3.client("iot", region_name=region_name).describe_endpoint(
        endpointType="iot:Data-ATS"
    )["endpointAddress"]


def GetIotMqttCommCfg(endpoint):
    if type(endpoint) == str:
        endpoint = str.encode(endpoint, "UTF-8")

    return (
        IOTMQTTCOMMCFG_HEADER
        + endpoint
        + (
            PADDING
            * (
                1
                + IOTMQTTCOMMCFG_LENGTH
                - len(IOTMQTTCOMMCFG_HEADER)
                - len(endpoint)
                - len(IOTMQTTCOMMCFG_FOOTER)
            )
        )
        + IOTMQTTCOMMCFG_FOOTER
    )


def GetIotMqttCommCredentials():
    return (
        b"\x02\x4f\x70\x74\x69\x63\x6f\x6d\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x47\x54\x54\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
        b"\x20\x20\x20\x20\x20\x20\x20\x00"
    )


def WriteIotCommCfgs(dck_names, region_name="us-east-1"):
    """[summary]
    Write the IoT Comm configs to the efs file system.
    Sleep is important , because once the docker is created it will take few
     seconds to create required files in the filesystem
    Arguments:
        dck_names {[string]} -- [docker name of the vps]
    """
    time.sleep(5)
    try:
        endpoint = GetIotEndpoint(region_name)
        with open(
            "/efs/{dckname}/misc_cfgs/IOTMQTTCommCfg".format(dckname=dck_names), "wb+"
        ) as f:
            f.write(GetIotMqttCommCfg(endpoint))

        with open(
            "/efs/{dckname}/misc_cfgs/IOTMQTTCredentialCfg".format(dckname=dck_names),
            "wb+",
        ) as f:
            f.write(GetIotMqttCommCredentials())
    except Exception as e:
        print(f"Failed to write IoT configurations to Intersection {dck_names}: '{e}'")
        raise e


def WriteCerts(dck_names):
    """[summary]
    Write the certificates to the efs file system.
    Sleep is important , because once the docker is created it will take few
     seconds to create required files in the filesystem
    Arguments:
        dck_names {[string]} -- [docker name of the vps]
    """
    time.sleep(5)
    try:
        input_zip = ZipFile(io.BytesIO(certificates))
        writelst = {
            name: input_zip.read(name).decode("utf-8") for name in input_zip.namelist()
        }
        with open(
            "/efs/{dckname}/comm_cfgs/deviceCert".format(dckname=dck_names), "wb+"
        ) as f:
            f.write(GetDeviceCert(writelst["cert.pem"]))
        with open(
            "/efs/{dckname}/comm_cfgs/deviceKey".format(dckname=dck_names), "wb+"
        ) as f:
            f.write(GetDeviceKey(writelst["key.key"]))
        with open(
            "/efs/{dckname}/comm_cfgs/rootCA".format(dckname=dck_names), "wb+"
        ) as f:
            f.write(GetRootCa(writelst["rootCA.pem"]))
        with open("/efs/{dckname}/comm_cfgs/CA".format(dckname=dck_names), "wb+") as f:
            f.write(GetCa(writelst["rootCA.pem"]))
    except Exception as e:
        print(f"Failed to write Certificates to Intersection {dck_names}: '{e}'")
        raise e


def SetDeviceRestart(
    primarKey,
    dynamoRegion=dynamoDBregion,
    dynamoTable=dynamoDBtable,
):
    try:
        boto3.client("dynamodb", region_name=dynamoRegion).transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "Key": {"primaryKey": {"N": str(primarKey)}},
                        "TableName": dynamoTable,
                        "UpdateExpression": "SET  deviceStatus =:deviceStatus ",
                        "ExpressionAttributeValues": {
                            ":deviceStatus": {"S": "RESTART"}
                        },
                    }
                }
            ]
        )
    except Exception as e:
        print(f"Failed to set Intersection {primarKey} to Restart: '{e}'")
        raise e


try:
    iteritems = dynamoResource.scan(
        FilterExpression=Attr("customerName").eq(args.customerName)
    )["Items"][0]["vpsSerial"]

    for x in iteritems:
        try:
            WriteGpsCfgs(
                x["latitude"], x["longitude"], x["intersectionName"], x["deviceName"]
            )
            WriteCerts(x["deviceName"])
            WriteIotCommCfgs(x["deviceName"], region_name=ec2_region)
            SetDeviceRestart(x["primaryKey"])
        except Exception:
            print(
                f"Failed to write configurations for Intersection {x['deviceName']} ({x['intersectionName']})"
            )
except Exception as e:
    print(f"Failed to write configurations to Intersections: '{e}'")

dynamoResource.update_item(
    Key={"customerName": args.customerName},
    UpdateExpression="set importInProgress = :r",
    ExpressionAttributeValues={":r": "false"},
)
