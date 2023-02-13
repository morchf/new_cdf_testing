import boto3
import time
from binascii import hexlify

PADDING = b"\x20"

IOTMQTTCOMMCFG_LENGTH = 267
# For the IOTMQTTCOMMCFG Header, the very first byte details
#  if test messages are on or off
#  \x00 means off, \x02 means on
IOTMQTTCOMMCFG_HEADER = b"\x00\x00\x00\x00\x02\x00\x00\x00"
IOTMQTTCOMMCFG_FOOTER = b"\x00\xB3\x22\x00\x00"

CERTIFICATEFILE_LENGTH = 4096
ROOTCA_HEADER = b"\x00"
CA_HEADER = b"\x01"
DEVICECERT_HEADER = b"\x02"
DEVICEKEY_HEADER = b"\x03"


def GetFileCopyCommand(filesToCopy, intersections):
    commands = []
    for pathTo in filesToCopy:
        hexString = hexlify(filesToCopy[pathTo]).decode()
        hexString = "\\x" + "\\x".join(
            [hexString[i : i + 2] for i in range(0, len(hexString), 2)]
        )
        commands.append(
            f"echo -n -e '{hexString}' | tee "
            f"{' '.join([f'/efs/{intersection}/{pathTo}' for intersection in intersections])}"  # noqa: E501
        )
    return commands


def SplitCommands(commands, maxsize):
    sets_of_commands = []
    commands_idx = 0
    while commands_idx < len(commands):
        temp_commands = []
        while sum([len(i) for i in temp_commands]) < maxsize and commands_idx < len(
            commands
        ):
            temp_commands.append(commands[commands_idx])
            commands_idx = commands_idx + 1
        if sum([len(i) for i in temp_commands]) >= maxsize:
            temp_commands = temp_commands[:-1]
            commands_idx = commands_idx - 1
        sets_of_commands.append(temp_commands)

    return sets_of_commands


def SendCommand(instanceid, intersections, filesToCopy, region_name=None):
    result = True
    client = (
        boto3.client("ssm")
        if region_name is None
        else boto3.client("ssm", region_name=region_name,)
    )
    commands = GetFileCopyCommand(filesToCopy, intersections)
    sets_of_commands = SplitCommands(commands, 50000)

    for commandsToRun in sets_of_commands:
        print(sum([len(i) for i in commandsToRun]))
        client.send_command(
            InstanceIds=[instanceid],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commandsToRun},
        )
        while True:
            time.sleep(2)
            commands = client.list_commands()["Commands"]
            most_recent_command = commands[0]
            most_recent_command_status = most_recent_command["Status"]
            if most_recent_command_status == "Failed":
                result = False
                break
            elif most_recent_command_status == "Success":
                break

    return result


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


def ConfigureIntersections(
    customerName,
    intersections=None,
    iotEndpoint=None,
    deviceCert=None,
    deviceKey=None,
    rootCa=None,
    approachMaps=True,
    region_name=None,
):
    ec2 = (
        boto3.client("ec2")
        if region_name is None
        else boto3.client("ec2", region_name=region_name)
    )
    response = ec2.describe_instances(
        Filters=[{"Name": "tag:aws:cloudformation:stack-name", "Values": ["HOKAH"]}]
    )
    # Greedy pick of the first EC2 matching that CustomerName
    instance_id = response["Reservations"][0]["Instances"][0]["InstanceId"]

    # Construct files to copy
    filesToCopy = {}
    if iotEndpoint is not None:
        filesToCopy["misc_cfgs/IOTMQTTCommCfg"] = GetIotMqttCommCfg(iotEndpoint)
        with open("Data/IOTMQTTCredentialCfg", "rb") as f:
            filesToCopy["misc_cfgs/IOTMQTTCredentialCfg"] = f.read()
    if deviceCert is not None:
        with open(deviceCert, "rb") as f:
            filesToCopy["comm_cfgs/deviceCert"] = GetDeviceCert(f.read())
    if deviceKey is not None:
        with open(deviceKey, "rb") as f:
            filesToCopy["comm_cfgs/deviceKey"] = GetDeviceKey(f.read())
    if rootCa is not None:
        with open(rootCa, "rb") as f:
            cert = f.read()
            filesToCopy["comm_cfgs/CA"] = GetCa(cert)
            filesToCopy["comm_cfgs/rootCA"] = GetRootCa(cert)
    if approachMaps:
        with open("Data/ApproachMaps", "rb") as f:
            filesToCopy["gps_cfgs/ApproachMaps"] = f.read()
    if intersections is None or intersections == []:
        intersections = ["*"]

    if not SendCommand(instance_id, intersections, filesToCopy, region_name):
        raise IOError("Failed to write configurations to intersections")
