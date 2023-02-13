import logging
import os
import time

import boto3
from botocore.auth import SigV4Auth  # noqa: E402
from botocore.awsrequest import AWSRequest  # noqa: E402
from botocore.endpoint import URLLib3Session  # noqa: E402
from pyspark.sql import DataFrame  # noqa: E402

__all__ = [
    "load_awsConfig",
    "send_request",
    "upload_cloudwatch_log",
    "unread_objects_s3",
    "tag_read_s3_objects",
    "fetch_s3data",
]


def load_awsConfig(aws_region=None) -> dict:
    aws_region = aws_region or os.environ["AWS_REGION"]
    headers = {
        "Accept": "application/vnd.aws-cdf-v2.0+json",
        "Content-Type": "application/vnd.aws-cdf-v2.0+json",
    }
    return {
        "aws_region": aws_region,
        "headers": headers,
    }


def send_request(url, method, region_name, params=None, headers=None):
    request = AWSRequest(
        method=method.upper(), url=url, data=params, headers=headers
    )  # noqa: E501
    SigV4Auth(
        boto3.Session().get_credentials(), "execute-api", region_name
    ).add_auth(  # noqa: E501
        request
    )
    return URLLib3Session().send(request.prepare()).content


##########################################
# Helper Methods for this PySpark Script #
##########################################


def upload_cloudwatch_log(message, awsConfig, envConfig) -> None:
    """Upload a log message to cloudwatch logs.

    Args:
        message (String): message to upload to cloudwatch log stream.
    """
    logging.info(message)
    log_client = boto3.client("logs", region_name=awsConfig["aws_region"])
    desc_response = log_client.describe_log_streams(
        logGroupName=envConfig.cloudwatch_log_group,
        logStreamNamePrefix=envConfig.cloudwatch_log_stream_name,
    )
    ts = int(time.time()) * 1000
    try:
        log_client.put_log_events(
            logGroupName=envConfig.cloudwatch_log_group,
            logStreamName=envConfig.cloudwatch_log_stream_name,
            logEvents=[
                {"timestamp": ts, "message": message},
            ],
            sequenceToken=desc_response["logStreams"][0][
                "uploadSequenceToken"
            ],  # noqa: E501
        )
    # create log stream prefix if it doesn't yet exist
    except IndexError:
        log_client.create_log_stream(
            logGroupName=envConfig.cloudwatch_log_group,
            logStreamName=envConfig.cloudwatch_log_stream_name,
        )
    except KeyError as ke:
        log_client.put_log_events(
            logGroupName=envConfig.cloudwatch_log_group,
            logStreamName=envConfig.cloudwatch_log_stream_name,
            logEvents=[
                {"timestamp": ts, "message": message + "error: " + str(ke)},
            ],
        )
    except log_client.exceptions.DataAlreadyAcceptedException:
        pass


def unread_objects_s3(awsConfig, envConfig) -> list:
    """Read the unread incoming messages in the S3 bucket under today's date.

    Returns:
        list: A list of unread objects to process later.
    """
    # 1. Connect to S3 bucket.
    # 3. Create a 'path_string' to access a folder in s3 bucket.
    # 4. Filter S3 objects which do not have the tag "Read", indicating this object is still not processed.

    # 1
    s3_client = boto3.client("s3", region_name=awsConfig["aws_region"])
    s3 = boto3.resource("s3")
    my_bucket = s3.Bucket(envConfig.incoming_bucket_name)  # type: ignore

    # 3
    # don't add extra '/' is incoming_s3_path is empty
    s3_filePath = (
        f"{envConfig.incoming_s3_path or ''}/utc_date={envConfig.source_date}"
    ).lstrip("/")
    not_read_objects = []

    # 4
    for object_summary in my_bucket.objects.filter(Prefix=f"{s3_filePath}"):
        key = object_summary.key
        if key.split("/")[-1] == "":
            continue
        response = s3_client.get_object_tagging(
            Bucket=envConfig.incoming_bucket_name, Key=key
        )  # noqa: E501
        try:
            # Check if a tag exists.
            response["TagSet"][0]["Key"]
        except:  # noqa: E722
            not_read_objects.append(key)
            continue
    return not_read_objects


def tag_read_s3_objects(awsConfig, envConfig) -> None:
    """This will be done after the processing, and it will tag the processed object with a "Read", indicating we've processed this object."""

    # 1. Find unread objects list.
    # 2. For each object, put the tag "Read".
    unread_objects = unread_objects_s3(awsConfig, envConfig)
    s3_client = boto3.client("s3", region_name=awsConfig["aws_region"])
    for obj in unread_objects:
        s3_client.put_object_tagging(
            Bucket=envConfig.incoming_bucket_name,
            Key=obj,
            Tagging={"TagSet": [{"Key": "Read", "Value": ""}]},
        )
    # Optional: A message that indicates we've processed this object.
    upload_cloudwatch_log(
        "Read objects tagged in S3 bucket for object: " + obj, awsConfig, envConfig
    )


def fetch_s3data(sparkSqlConfig, awsConfig, envConfig) -> DataFrame:
    """Go into S3 and store the incoming 'unprocessed' message as a DataFrame.

    Returns:
        DataFrame: Get the processed pyspark's dataframe from S3, which would be a List of PySpark.Rows
    """
    # 1. Get a list of unread objects from S3.
    # 2. Create the local directories "incoming_MP70_msg_local_copy" and "processed_MP70_msg_local_copy", which will store the respective files locally.
    # 3. Iterate over the array and download each file from S3 into the incoming messages folder locally.
    # 4. Get Processed DataFrame of the objects, which will be later used to create rt_message.

    s3 = boto3.client("s3", region_name=awsConfig["aws_region"])
    mode = f"{envConfig.device_model}_{envConfig.device_operational_mode}"

    # 1
    unread_filepaths = unread_objects_s3(awsConfig, envConfig)
    local_filenames = [
        f"incoming_{mode}_msg_local_copy/{filename.split('/')[-1]}.txt"
        for filename in unread_filepaths
    ]
    if len(unread_filepaths) == 0:
        upload_cloudwatch_log("No new Unread files found today", awsConfig, envConfig)
        os._exit(os.EX_OK)

    # 2
    if not os.path.exists(f"incoming_{mode}_msg_local_copy"):
        os.mkdir(f"incoming_{mode}_msg_local_copy")
    if not os.path.exists(f"processed_{mode}_msg_local_copy"):
        os.mkdir(f"processed_{mode}_msg_local_copy")
    for s3_filepath, local_filename in zip(unread_filepaths, local_filenames):
        print(f"downloading {s3_filepath=}")
        s3.download_file(
            envConfig.incoming_bucket_name,
            s3_filepath,
            local_filename,
        )  # noqa: E501

    processed_df = sparkSqlConfig["spark"].read.json(
        f"incoming_{mode}_msg_local_copy/*.txt"
    )

    return processed_df
