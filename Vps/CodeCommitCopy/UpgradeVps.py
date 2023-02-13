import boto3
from boto3.dynamodb.conditions import Attr
import base64
import docker
import requests
from requests.exceptions import HTTPError
import subprocess
import os
import sys

cache = {}
recursion_counter = 0


def getDockerImage(client, agencyName, version="latest"):
    try:
        return cache[version]
    except Exception:
        pass

    # Setup Clients
    ecr_client = boto3.client("ecr", region_name="us-east-1")

    # Get Login for ECR
    token = ecr_client.get_authorization_token()
    username, password = (
        base64.b64decode(token["authorizationData"][0]["authorizationToken"])
        .decode()
        .split(":")
    )
    registry = token["authorizationData"][0]["proxyEndpoint"]
    client.login(username, password, registry=registry)

    # Pull Image
    docker_image = (
        boto3.resource("dynamodb", region_name="us-east-1")
        .Table("codeBuildDeploy")
        .scan(FilterExpression=Attr("customerName").eq(agencyName))["Items"][0][
            "dockerImage"
        ]
    ).split(":")[0]
    response = client.images.pull(
        docker_image,
        tag=version,
        auth_config={"username": username, "password": password},
    )

    # Return the image tag if successful
    img = f"{docker_image}:{version}"
    if img in response.tags:
        cache[version] = img
        return img


def getDockerStatus(dockerName):
    return docker.APIClient().inspect_container(dockerName)


def runDockerContainer(
    client, agencyName, dockerName, dockerImage, dockerPort, macAddress, efsName=None
):
    efsName = efsName if efsName is not None else dockerName
    client.containers.run(
        name=dockerName,
        hostname=dockerName,
        image=dockerImage,
        detach=True,
        ports={"5000/tcp": dockerPort},
        restart_policy={"Name": "unless-stopped"},
        volumes={f"/efs/{efsName}": {"bind": "/root", "mode": "rw"}},
        mem_limit="25m",
        log_config=dict(
            type="awslogs",
            config={
                "awslogs-group": f"/vps/{agencyName}",
                "awslogs-create-group": "true",
                "awslogs-stream": f"{dockerName}",
            },
        ),
        mac_address=macAddress,
        nano_cpus=50000000,
        cpu_count=0,
        cpu_percent=0,
        cpu_period=0,
        cpu_quota=0,
        cpu_rt_period=0,
        cpu_rt_runtime=0,
        cpu_shares=0,
    )


def startDockerContainer(client, dockerName):
    return client.containers.get(dockerName).start()


def stopDockerContainer(client, dockerName):
    return client.containers.get(dockerName).stop()


def removeDockerContainer(client, dockerName):
    return client.containers.get(dockerName).remove()


def renameDockerContainer(client, dockerName, newDockerName):
    return client.containers.get(dockerName).rename(newDockerName)


def getAgencyName():
    r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
    response_json = r.json()
    ec2_region = response_json.get("region")
    instance_id = response_json.get("instanceId")
    ec2 = boto3.resource("ec2", region_name=ec2_region)
    instance = ec2.Instance(instance_id)
    tags = instance.tags
    agencyName = [tag.get("Value") for tag in tags if tag.get("Key") == "AGENCY"][0]
    return agencyName


def checkNumericalVersion(v1, v2):
    version_parts1 = v1.split(".")
    version_parts2 = v2.split(".")
    if int(version_parts2[0]) < int(version_parts1[0]):
        return {
            "statusCode": 400,
            "body": "Docker version requested would result in downgrading the software",
        }
    elif int(version_parts2[0]) == int(version_parts1[0]):
        if int(version_parts2[1]) < int(version_parts1[1]):
            return {
                "statusCode": 400,
                "body": "Docker version requested would result in "
                "downgrading the software",
            }
        elif int(version_parts2[1]) == int(version_parts1[1]):
            if int(version_parts2[2]) < int(version_parts1[2]):
                return {
                    "statusCode": 400,
                    "body": "Docker version requested would result in "
                    "downgrading the software",
                }
    return {"statusCode": 200, "body": "OK"}


def checkLatestUpgrade(client, dockerName, current_version, requested_version):
    local_digest = getDockerStatus(dockerName)["Image"]
    requested_digest = client.images.get(requested_version).attrs["Id"]

    if local_digest == requested_digest:
        return {
            "statusCode": 201,
            "body": "Docker version already matches the requested version",
        }
    else:
        return {"statusCode": 200, "body": "OK"}


def checkVersion(client, dockerName, current_version, requested_version):
    current_version_tag = current_version.split(":")[-1]
    requested_version_tag = requested_version.split(":")[-1]

    if (
        current_version == requested_version
        and current_version.split(":")[-1] != "latest"
    ):
        return {
            "statusCode": 201,
            "body": "Docker version already matches the requested version",
        }

    if current_version_tag == "latest" and requested_version_tag != "latest":
        # Disallow upgrading from latest to anything but latest
        return {
            "statusCode": 400,
            "body": "Docker version requested would result in downgrading the software",
        }
    elif current_version_tag != "latest" and requested_version_tag == "latest":
        # Allow upgrading from latest to anything
        return {"statusCode": 200, "body": "OK"}
    elif current_version_tag != "latest" and requested_version_tag != "latest":
        # Check for downgrading if neither are latest
        return checkNumericalVersion(current_version_tag, requested_version_tag)
    elif current_version_tag == "latest" and requested_version_tag == "latest":
        # Check if upgrade is needed using digests
        return checkLatestUpgrade(
            client, dockerName, current_version, requested_version
        )
    else:
        # Nothing should ever hit this check
        return {
            "statusCode": 400,
            "body": "Unknown Internal Error",
        }


def validateDocker(client, dockerName, expectedNonVersion, availableDockerImages=None):
    # Check that the requested version exists
    if availableDockerImages is None:
        availableDockerImages = [j for i in client.images.list() for j in i.tags]
    if expectedNonVersion not in availableDockerImages:
        return {"statusCode": 404, "body": "Requested VPS Version not available"}

    # Validate docker exists and is running
    try:
        status = getDockerStatus(dockerName)
        if status["State"]["Status"] != "running":
            try:
                if recursion_counter > 5:
                    raise ValueError("Unable to start docker container")
                startDockerContainer(client, dockerName)
            except Exception:
                return {"statusCode": 500, "body": "Unable to start docker container"}
            return validateDocker(
                client, dockerName, expectedNonVersion, availableDockerImages
            )
    except Exception as e:
        # Catch only 404 errors to give better error messages
        if (
            isinstance(e, HTTPError)
            and e.response.status_code == 404  # pylint: disable=no-member
        ):
            return {"statusCode": 404, "body": "Docker container does not exist"}
        else:
            return {"statusCode": 500, "body": "Internal Server Error"}

    # Validate that the version would not result in downgrading the docker container
    return checkVersion(
        client, dockerName, status["Config"]["Image"], expectedNonVersion
    )


def copyDirectoryRecursive(pathfrom, pathto):
    output = subprocess.run(
        ["sudo", "cp", "-r", pathfrom, pathto],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    if output.returncode != 0:
        raise IOError("Unable to copy directory")


def deleteDirectoryRecursive(path):
    output = subprocess.run(
        ["sudo", "rm", "-r", path], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    if output.returncode != 0:
        raise IOError("Unable to delete directory")


def getPrimaryKey(agencyName, dockerName):
    table = boto3.resource("dynamodb", region_name="us-east-1").Table("globalMacVps")

    scan_kwargs = {
        "FilterExpression": Attr("VPS").eq(dockerName)
        & Attr("customerName").eq(agencyName),
        "ProjectionExpression": "primaryKey, VPS, dockerIP",
    }

    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key
        response = table.scan(**scan_kwargs)
        items = response.get("Items")
        if items != [] and items is not None:
            break
        start_key = response.get("LastEvaluatedKey", None)
        done = start_key is None

    return items[0]["primaryKey"]


def updateDynamoDb(agencyName, dockerName, requestedVersion):
    try:
        primaryKey = getPrimaryKey(agencyName, dockerName)

        table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "globalMacVps"
        )
        table.update_item(
            Key={"primaryKey": primaryKey},
            UpdateExpression="SET dockerImage = :image",
            ExpressionAttributeValues={":image": requestedVersion},
        )
    except Exception:
        return {
            "statusCode": 500,
            "body": "Non-Fatal Error: Unable to update Dynamo DB"
            "with the new VPS version",
        }

    return {"statusCode": 200, "body": "Updated DynamoDB record"}


def rollbackDockerStatus(client, dockerName, status):
    # Start Original Docker
    try:
        if getDockerStatus(dockerName)["State"]["Status"] != "running":
            startDockerContainer(client, dockerName)
    except Exception:
        status.append(
            {
                "statusCode": 500,
                "body": "Rolling Back: Failed to start up original docker container",
            }
        )

    # Delete Backup Filesystem
    try:
        failuresRollingBack = ["Rolling Back:" in i["body"] for i in status]
        if os.path.exists(f"/efs/{dockerName}_TemporaryDirectory") and not any(
            failuresRollingBack
        ):
            deleteDirectoryRecursive(f"/efs/{dockerName}_TemporaryDirectory")
    except Exception:
        status.append(
            {
                "statusCode": 500,
                "body": "Rolling Back: Failed to delete temporary directory "
                "for VPS file system",
            }
        )

    status.append({"statusCode": 200, "body": "Rolling Back: Rollback Complete"})

    return status


def rollbackDockerUpgrade(client, dockerName, status):
    # Stop dockerName Docker if needed
    try:
        if getDockerStatus(dockerName)["State"]["Status"] == "running":
            stopDockerContainer(client, dockerName)
    except Exception as e:
        if (
            isinstance(e, HTTPError)
            and e.response.status_code == 404  # pylint: disable=no-member
        ):
            pass
        else:
            status.append(
                {
                    "statusCode": 500,
                    "body": f"Rolling Back: Unable to stop Docker {dockerName}",
                }
            )

    # Copy Backup files back to VPS file system
    try:
        copyDirectoryRecursive(
            f"/efs/{dockerName}_TemporaryDirectory", f"/efs/{dockerName}"
        )
    except Exception:
        status.append(
            {
                "statusCode": 500,
                "body": "Rolling Back: Failed to write VPS Backup filesystem "
                "to VPS filesystem",
            }
        )

    # Check if {dockerName}_TEMP_OLD exists
    try:
        getDockerStatus(f"{dockerName}_TEMP_OLD")
        try:
            getDockerStatus(dockerName)
            removeDockerContainer(client, dockerName)
        except Exception as e:
            if (
                isinstance(e, HTTPError)
                and e.response.status_code == 404  # pylint: disable=no-member
            ):
                pass
            else:
                status.append(
                    {
                        "statusCode": 500,
                        "body": f"Rolling Back: Failed to delete Docker {dockerName}.",
                    }
                )

        try:
            renameDockerContainer(client, f"{dockerName}_TEMP_OLD", dockerName)
        except Exception:
            status.append(
                {
                    "statusCode": 500,
                    "body": "Rolling Back: Failed to rename "
                    f"{dockerName}_TEMP_OLD to {dockerName}",
                }
            )
    except Exception as e:
        if (
            isinstance(e, HTTPError)
            and e.response.status_code == 404  # pylint: disable=no-member
        ):
            pass
        else:
            status.append(
                {
                    "statusCode": 500,
                    "body": "Rolling Back: Failed to restore "
                    f"{dockerName}_TEMP_OLD to {dockerName}",
                }
            )

    # Delete {dockerName}_TEMP_NEW if exists and start dockerName if needed
    try:
        getDockerStatus(f"{dockerName}_TEMP_NEW")
        try:
            stopDockerContainer(client, f"{dockerName}_TEMP_NEW")
        except Exception:
            status.append(
                {
                    "statusCode": 500,
                    "body": f"Rolling Back: Failed to stop {dockerName}_TEMP_NEW.",
                }
            )

        try:
            removeDockerContainer(client, f"{dockerName}_TEMP_NEW")
        except Exception:
            status.append(
                {
                    "statusCode": 500,
                    "body": "Rolling Back: Failed to remove "
                    f"container {dockerName}_TEMP_NEW",
                }
            )
    except Exception as e:
        if (
            isinstance(e, HTTPError)
            and e.response.status_code == 404  # pylint: disable=no-member
        ):
            pass
        else:
            status.append(
                {
                    "statusCode": 500,
                    "body": f"Rolling Back: Failed to get {dockerName}_TEMP_NEW status",
                }
            )

    try:
        startDockerContainer(client, dockerName)
    except Exception:
        status.append(
            {
                "statusCode": 500,
                "body": f"Rolling Back: Failed to start Docker Container {dockerName}",
            }
        )

    return rollbackDockerStatus(client, dockerName, status)


def upgradeDockerContainer(client, agencyName, dockerName, requestedVersion):
    status = []

    # Stop current docker container
    try:
        stopDockerContainer(client, dockerName)
    except Exception:
        status.append({"statusCode": 500, "body": "Failed to stop docker container"})
        return rollbackDockerStatus(client, dockerName, status)

    # For each valid request, copy VPS files to temporary directory
    try:
        deleteDirectoryRecursive(f"/efs/{dockerName}_TemporaryDirectory")
    except Exception:
        pass

    try:
        copyDirectoryRecursive(
            f"/efs/{dockerName}", f"/efs/{dockerName}_TemporaryDirectory"
        )
    except Exception:
        status.append({"statusCode": 500, "body": "Failed to backup VPS Filesystem"})
        return rollbackDockerStatus(client, dockerName, status)

    # Create and run new docker container
    try:
        dockerStatus = getDockerStatus(dockerName)
        runDockerContainer(
            client,
            agencyName,
            f"{dockerName}_TEMP_NEW",
            requestedVersion,
            dockerStatus["HostConfig"]["PortBindings"]["5000/tcp"][0]["HostPort"],
            dockerStatus["Config"]["MacAddress"],
            efsName=f"{dockerName}",
        )
    except Exception:
        status.append(
            {"statusCode": 500, "body": "Failed to create new docker container"}
        )
        return rollbackDockerUpgrade(client, dockerName, status)

    # Rename docker containers
    try:
        renameDockerContainer(client, dockerName, f"{dockerName}_TEMP_OLD")
        renameDockerContainer(client, f"{dockerName}_TEMP_NEW", dockerName)
    except Exception:
        status.append({"statusCode": 500, "body": "Failed to rename docker containers"})
        return rollbackDockerUpgrade(client, dockerName, status)

    # Delete old docker container
    try:
        removeDockerContainer(client, f"{dockerName}_TEMP_OLD")
    except Exception:
        status.append(
            {
                "statusCode": 500,
                "body": "Non-Fatal Error: Failed to remove "
                "old stopped docker container",
            }
        )

    # Try Except Occurs within the function
    status.append(updateDynamoDb(agencyName, dockerName, requestedVersion))

    try:
        deleteDirectoryRecursive(f"/efs/{dockerName}_TemporaryDirectory")
    except Exception:
        status.append(
            {
                "statusCode": 500,
                "body": "Non-Fatal Error: Failed to delete temporary backup files",
            }
        )

    status.append({"statusCode": 200, "body": "OK"})

    return status


def upgradeDockerContainers(requested):
    """Robustly attempts to upgrade each docker image in the requests argument
        to the requested version

    Arguments:
        requested {[dict]} -- dictionary of docker image name to requested version
                               (both in strings)
            eg - {"V764NBTEST1": "10.03.004", "V764NBTEST2": "10.03.004"}
    """
    client = docker.from_env()
    agencyName = getAgencyName()
    status = {}

    # Download any needed docker images (it caches for speed)
    for i in requested:
        try:
            requested[i] = getDockerImage(client, agencyName, requested[i])
        except Exception:
            pass
    availableDockerImages = [j for i in client.images.list() for j in i.tags]

    # Validate that each docker being requested exists, is running and
    #  is not at the requested version
    for i in requested:
        global recursion_counter
        recursion_counter = 0
        status[i] = {
            "Validation": validateDocker(client, i, requested[i], availableDockerImages)
        }

    # For each valid request, upgrade the docker or update DynamoDB
    #  if no upgrade is required
    for i in requested:
        if status[i]["Validation"]["statusCode"] == 200:
            status[i]["UpdateDocker"] = upgradeDockerContainer(
                client, agencyName, i, requested[i]
            )
        elif status[i]["Validation"]["statusCode"] == 201:
            status[i]["UpdateDocker"] = [
                {"statusCode": 200, "body": "No upgrade to VPS software required"}
            ]
            status[i]["UpdateDocker"].append(
                updateDynamoDb(agencyName, i, requested[i])
            )
        else:
            updateDynamoDb(agencyName, i, getDockerStatus(i)["Config"]["Image"])

    return status


if __name__ == "__main__":
    requested = {}
    for i in range(1, len(sys.argv)):
        parts = sys.argv[i].split("=")
        requested[parts[0]] = parts[1]

    status = upgradeDockerContainers(requested)
    print(status)
