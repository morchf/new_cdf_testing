import os

import boto3
from botocore.exceptions import ClientError
from pyspark import SparkContext  # noqa: E402
from pyspark.sql import SparkSession, SQLContext  # noqa: E402

from data_aggregation.Utils.AwsUtil import upload_cloudwatch_log

__all__ = [
    "load_sparkSqlConfig",
    "append_cdf_info",
    "upload_directory",
    "write_by_agency_id",
]


def load_sparkSqlConfig() -> dict:
    # configure
    spark = SparkSession.builder.master("local").getOrCreate()
    sc = SparkContext.getOrCreate()
    sqlContext = SQLContext(sc)
    return {
        "spark": spark,
        "sc": sc,
        "sqlContext": sqlContext,
    }


def append_cdf_info(message_details, client_id, awsConfig, envConfig) -> dict:
    """Append CDF details that are stored in cache to the message dict.

    Args:
        message_details (dict): message details used to create rt_message.
        client_id (String): to access a particular record in cache.

    Returns:
        dict: the complete message details as dict needed to create an rt_message.
    """
    try:
        message_details = {
            **message_details,
            **envConfig.device_dict[client_id.lower()],
        }
    except Exception as e:
        upload_cloudwatch_log(
            "Error in appending CDF information: " + str(e), awsConfig, envConfig
        )
    return message_details


def upload_directory(path, bucketname, s3_objPath, awsConfig, envConfig) -> bool:
    """Upload the processed file in S3.

    Args:
        path (String): Local path of the processed messages file.
        bucketname (String): S3 bucket name to store the parquet file.
        s3_objPath (String): Path in s3 to store the parquet file.

    Returns:
        bool: True -> Successfully stored the file in S3.
              False -> Error in storing file in S3.
    """
    s3 = boto3.resource("s3")
    for root, _, files in os.walk(path):
        for file in files:
            try:
                s3.meta.client.upload_file(
                    os.path.join(root, file),
                    bucketname,
                    str(s3_objPath + "/" + file),  # noqa: E501
                )
            except ClientError as e:
                upload_cloudwatch_log(str(e), awsConfig, envConfig)
                return False
    return True


def write_by_agency_id(awsConfig, envConfig):
    """Walk through the processed messages local directory and upload the processed messages 'parquet' file to S3 for a particular agency."""

    # Upload the files to S3 from the local environment
    mode = f"{envConfig.device_model}_{envConfig.device_operational_mode}"
    for _, dirs, _ in os.walk(f"processed_{mode}_msg_local_copy"):
        if len(dirs) != 0:
            for id_folder in dirs:
                agency_id = id_folder.split("=")[1]
                # don't add extra '/' is outgoing_s3_path is empty
                s3_filePath = (
                    f"{envConfig.outgoing_s3_path or ''}/"
                    f"agency_id={agency_id}/"
                    f"utc_date={envConfig.source_date}/"
                    f"source_device={envConfig.device_model}-{envConfig.device_operational_mode}"
                ).lstrip("/")
                upload_directory(
                    f"processed_{mode}_msg_local_copy/{id_folder}",
                    envConfig.outgoing_bucket_name,
                    s3_filePath,  # noqa: E501
                    awsConfig,
                    envConfig,
                )  # noqa: E501

    upload_cloudwatch_log("Written processed message to s3", awsConfig, envConfig)
