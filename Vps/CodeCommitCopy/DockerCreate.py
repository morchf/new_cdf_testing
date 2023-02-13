import base64
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import boto3
import docker
import requests
from boto3.dynamodb.conditions import Attr, Key
from tenacity import retry, stop_after_attempt, wait_random

dynamoDBregion = "us-east-1"
dynamoDBtable = "globalMacVps"
client = docker.from_env()

table = boto3.resource("dynamodb", region_name=dynamoDBregion).Table(dynamoDBtable)
r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
response_json = r.json()
ec2_region = response_json.get("region")
instance_id = response_json.get("instanceId")
ec2 = boto3.resource("ec2", region_name=ec2_region)
instance = ec2.Instance(instance_id)
tags = instance.tags
inst_name_tags = [tag.get("Value") for tag in tags if tag.get("Key") == "serverName"]
name = inst_name_tags[0]
dockerPorts = []
agencyName = [tag.get("Value") for tag in tags if tag.get("Key") == "AGENCY"][0]
ecr_client = boto3.client("ecr", region_name="us-east-1")
# CREATE CLOUDWATCH GROUP OF EACH DOCKER
s3syncFolder = (
    boto3.resource("dynamodb", region_name="us-east-1")
    .Table("codeBuildDeploy")
    .query(KeyConditionExpression=Key("customerName").eq("GTT"))["Items"][0][
        "S3BACKUPFOLDER"
    ]
)
todayDT = date.today().strftime("%d-%m-%Y")
# PULL DOCKER IMAGE FROM THE ECR
token = ecr_client.get_authorization_token()
username, password = (
    base64.b64decode(token["authorizationData"][0]["authorizationToken"])
    .decode()
    .split(":")
)
registry = token["authorizationData"][0]["proxyEndpoint"]
client.login(username, password, registry=registry)
docker_image = (
    boto3.resource("dynamodb", region_name="us-east-1")
    .Table("codeBuildDeploy")
    .scan(FilterExpression=Attr("customerName").eq(agencyName))["Items"][0][
        "dockerImage"
    ]
)

client.images.pull(
    docker_image,
    tag="latest",
    auth_config={"username": username, "password": password},
)
# docker_image = "docker.pkg.github.com/gtt/dockersmartcity/smartcityvps:1.0"
# client.login(
#     "pruthvirajksuresh",
#     "3ef13e7d46acf8bb291a96ae8b6044ba71c6520b",
#     registry="http://docker.pkg.github.com",
# )
# client.images.pull(
#     "docker.pkg.github.com/gtt/dockersmartcity/smartcityvps",
#     tag="1.0",
#     auth_config={
#         "username": "pruthvirajksuresh",
#         "password": "3ef13e7d46acf8bb291a96ae8b6044ba71c6520b",
#     },
# )


################################################################

# get all docker info in that server
docker_boto_dynamo = table.scan(
    FilterExpression=Attr("serverName").eq(name),
    ProjectionExpression="primaryKey,VPS,GTTmac,deviceStatus,dockerPort,markToDelete",
)["Items"]


def updateDockerInfo(
    primarKey,
    dockerName,
    dockerStatus,
    dynamoRegion,
    dynamoTable,
    instanceiD=response_json["instanceId"],
):
    """[summary]
        updateDockerInfo function updates the docker info to the dynamo db table,
         as well as starting and stopping the container as per the status that
         is indcated in the dynmao db
    Arguments:
        primaryKey {[Integer]} -- [unique key of the dynamodb table]
        dockerName {[String]} -- [VPS names]
        dockerStatus {[String]} -- [docker status ({"ACTIVE":"running",
         "INACTIVE":"exited","terminated":{"docker is set to delete"})]
        dynamoRegion {[String]} -- [dynamo db region name]
        dynamoTable {[String]} -- [dynamo db table name]
    """
    if dockerStatus == "ACTIVE":
        client.containers.get(dockerName).start()
    elif dockerStatus == "INACTIVE":
        client.containers.get(dockerName).stop()
    elif dockerStatus == "RESTART":
        client.containers.get(dockerName).restart()
        boto3.client("dynamodb", region_name=dynamoRegion).transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "Key": {"primaryKey": {"N": str(primarKey)}},
                        "TableName": dynamoTable,
                        "UpdateExpression": "SET  deviceStatus =:deviceStatus ",
                        "ExpressionAttributeValues": {":deviceStatus": {"S": "ACTIVE"}},
                    }
                }
            ]
        )
    dockString = docker.APIClient().inspect_container(dockerName)
    dockStatus = dockString["State"]["Status"]
    dockStarted = dockString["State"]["StartedAt"]
    dockFinished = dockString["State"]["FinishedAt"]
    dockImage = dockString["Config"]["Image"]
    dockerPort = int(
        dockString["HostConfig"]["PortBindings"]["5000/tcp"][0]["HostPort"]
    )
    dockIP = str(
        requests.get("http://169.254.169.254/latest/meta-data/local-ipv4").content,
        "utf-8",
    )
    boto3.client("dynamodb", region_name=dynamoRegion).transact_write_items(
        TransactItems=[
            {
                "Update": {
                    "Key": {"primaryKey": {"N": str(primarKey)}},
                    "TableName": dynamoTable,
                    "UpdateExpression": "SET  dockerStatus =:dockStatus , "
                    "dockerIP =:dockIP , dockerPort =:dockPort ,"
                    "dockerStart =:dockStart, dockerFinished= :dockFinish, "
                    "lastCheck= :lastCheck , dockerImage= :dckImage , "
                    "dockerInstanceID= :dckInstanceID ",
                    "ExpressionAttributeValues": {
                        ":dockStatus": {"S": dockStatus},
                        ":dockIP": {"S": dockIP},
                        ":dockPort": {"N": str(dockerPort).zfill(4)},
                        ":dockStart": {"S": dockStarted},
                        ":dockFinish": {"S": dockFinished},
                        ":lastCheck": {
                            "S": datetime.now().strftime("%m-%d-%YT%H:%M:%S.%f")
                        },
                        ":dckImage": {"S": dockImage},
                        ":dckInstanceID": {"S": instanceiD},
                    },
                }
            }
        ]
    )


@retry(
    wait=wait_random(0, 3) + wait_random(1, 3),
    stop=stop_after_attempt(10),
    reraise=True,
)
def docker_create(
    primaryKey,
    dck_names,
    docker_img,
    dck_port,
    dck_status,
    dck_delete,
    mac_address,
    dynamoRegion,
    dynamoTable,
    agency_name,
):
    """[summary]
        docker_create function will create the dockers on the hosted server, with
         the settings specified in the dynmaoDB
    Arguments:
        primaryKey {[Integer]} -- [unique key of the dynamodb table]
        dck_names {[String]} -- [VPS names]
        docker_img {[String]} -- [docker Images]
        dck_port {[Integer]} -- [docker port number]
        dck_status {[String]} -- [docker status ({"ACTIVE":"running",
         "INACTIVE":"exited","terminated":{"docker is set to delete"})]
        dck_delete {[String]} -- [docker set to delete ? ({"NO":"DON'T DELETE",
         "YES":"DELETE THE CONTAINER NOT THE RECORD IN DYNMAODB"})]
        mac_address {[String]} -- [Global unique mac address]
        dynamoRegion {[String]} -- [dynamo db region name]
        dynamoTable {[String]} -- [dynamo db table name]
    """
    if dck_delete == "NO":
        try:
            updateDockerInfo(
                primaryKey, dck_names, dck_status, dynamoRegion, dynamoTable
            )
        except docker.errors.NotFound:
            # create a path/folder to store config data
            dir_path = Path("/efs", dck_names)
            defaults = (Path(__file__).parent / "default_config").resolve()
            if defaults.exists():
                shutil.copytree(src=str(defaults), dst=str(dir_path))
            else:
                print(f"Couldn't find defaults folder at: {defaults}")
                os.system("sudo mkdir -m 777 -p " + dir_path)
            client.containers.run(
                name=dck_names,
                hostname=dck_names,
                image=docker_img,
                detach=True,
                ports={"5000/tcp": int(dck_port)},
                restart_policy={"Name": "unless-stopped"},
                volumes={str(dir_path): {"bind": "/root", "mode": "rw"}},
                mem_limit="25m",
                # write logs to the cloudwatch event
                log_config=dict(
                    type="awslogs",
                    config={
                        "awslogs-group": f"/vps/{agencyName}",
                        "awslogs-create-group": "true",
                        "awslogs-stream": f"{dck_names}",
                    },
                ),
                # memswap_limit="50m",
                mac_address=mac_address,
                nano_cpus=50000000,
                cpu_count=0,
                cpu_percent=0,
                cpu_period=0,
                cpu_quota=0,
                cpu_rt_period=0,
                cpu_rt_runtime=0,
                cpu_shares=0,
            )
            updateDockerInfo(
                primaryKey, dck_names, dck_status, dynamoRegion, dynamoTable
            )
    elif dck_delete == "YES":
        try:
            client.containers.get(dck_names).stop()
            client.containers.get(dck_names).remove()
            boto3.client("dynamodb", region_name=dynamoRegion).transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "Key": {"primaryKey": {"N": str(primaryKey)}},
                            "TableName": dynamoTable,
                            "UpdateExpression": "SET  dockerStatus =:dockStatus, "
                            "dockerPort =:dockPort, lastCheck= :lastCheck ",
                            "ExpressionAttributeValues": {
                                ":dockStatus": {"S": "TERMINATED"},
                                ":dockPort": {"N": str("0000").zfill(4)},
                                ":lastCheck": {
                                    "S": datetime.now().strftime("%m-%d-%YT%H:%M:%S.%f")
                                },
                            },
                        }
                    }
                ]
            )
        except Exception:
            pass


emptyPort = [x for x in docker_boto_dynamo if x.get("dockerPort", "null") == "null"]
NONemptyPort = [x for x in docker_boto_dynamo if x.get("dockerPort", "null") != "null"]
# GETLIST OF ALL AVAILABLE DOCKERS
for item in [
    docker.APIClient().inspect_container(container.id)["NetworkSettings"]["Ports"]
    for container in client.containers.list()
]:
    if "5000/tcp" in item:
        dockerPorts.append(int(item.get("5000/tcp", None)[0]["HostPort"]))
########################################################################################
portNBER = 2000 if len(dockerPorts) == 0 else max(dockerPorts) + 1
i = 0
while i < len(emptyPort):
    emptyPort[i].update({"dockerPort": i + portNBER})
    i += 1

newList = emptyPort + NONemptyPort
for item in newList:
    docker_create(
        int(item["primaryKey"]),
        item["VPS"],
        docker_image,
        item["dockerPort"],
        item["deviceStatus"],
        item["markToDelete"],
        item["GTTmac"],
        dynamoDBregion,
        dynamoDBtable,
        agencyName,
    )

# sync efs info into s3
if "1" in name:
    os.system(f"sudo aws s3 sync /efs/ s3://{s3syncFolder}/{agencyName}/{todayDT}")
