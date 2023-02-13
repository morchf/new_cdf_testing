import boto3
import json
import io
import redis
import os
import datetime

# Using the environment variables for getting the endpoint urls and port numbers
CLUSTER_URL = os.environ["env_node_endpoint"].split(":")[0]
PORT = os.environ["env_node_endpoint"].split(":")[1]
ENV = os.environ["Env"]
FIRM_VER_BUCKET = "firmware-history-" + ENV
FILE_NAME = (
    "date_ran="
    + datetime.datetime.now().strftime("%Y-%m-%d")
    + "/firmware_version_and_date.json"
)


# Role needs to be UpdateFirmwareVersionToElasticache


def lambda_handler(event, context):
    try:
        s3 = boto3.client("s3")
        result = s3.list_objects(Bucket=FIRM_VER_BUCKET)
        # get the latest object in the firmware version bucket based on date_ran
        latest_date_ran = None
        for file in result["Contents"]:
            if "date_ran" in str(file["Key"]):
                date_ran = str(file["Key"]).split("/")[-2].split("=")[1]
                if latest_date_ran is None or date_ran > latest_date_ran:
                    latest_date_ran = date_ran
        version_date_obj = s3.get_object(
            Bucket=FIRM_VER_BUCKET,
            Key="date_ran=" + latest_date_ran + "/" + FILE_NAME,
        )
        version_data = json.load(io.BytesIO(version_date_obj["Body"].read()))

        # connect to elasticache and set key as the serial number and firmware version and date as a nested dictionary.
        r = redis.Redis(host=CLUSTER_URL, port=PORT, db=0)
        for i in version_data:
            for ver in sorted(version_data[i].keys()):
                # push the version history and date as a dictionary
                r.lpush(i, json.dumps({str(ver): str(version_data[i][ver])}))
        print("Updating the elasticache with firmware version and date is complete")

    except Exception as e:
        print("There is an Exception while running the lambda")
        print(e)
