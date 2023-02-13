import importlib
import logging
import os
from argparse import ArgumentParser
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from data_aggregation.Utils.AwsUtil import (
    load_awsConfig,
    tag_read_s3_objects,
    upload_cloudwatch_log,
)
from data_aggregation.Utils.Common import load_sparkSqlConfig, write_by_agency_id


@dataclass
class Config:
    aws_region: str
    cdf_url: str
    device_model: Literal["2100, 2101, MP70"]
    device_operational_mode: Literal["TSP", "EVP"]
    cloudwatch_log_group: str
    cloudwatch_log_stream_name: str
    incoming_bucket_name: str
    outgoing_bucket_name: str
    incoming_s3_path: str
    outgoing_s3_path: str
    # used to get unread_objects_s3
    source_date: str = datetime.utcnow().date()
    # used for caching rt radio message metadata
    device_dict: dict = field(default_factory=dict)


def write_back_to_s3(config: Config):
    sparkSqlConfig = load_sparkSqlConfig()
    awsConfig = load_awsConfig(config.aws_region)

    upload_cloudwatch_log(str(config), awsConfig, config)

    # import the correct version of process_data based on model/operational_mode
    process_data = (
        importlib.import_module("data_aggregation.2100.Base_2100").process_data
        if config.device_model in ["2100", "2101"]
        else importlib.import_module("data_aggregation.MP70.Base_MP70").process_data
    )

    # 1.
    final_df = process_data(sparkSqlConfig, awsConfig, config)

    filename = f"processed_{config.device_model}_{config.device_operational_mode}_msg_local_copy"

    # 2.
    final_df.write.partitionBy("AgencyID").mode("overwrite").parquet(filename)

    # 3.
    write_by_agency_id(awsConfig, config)

    # 4.
    tag_read_s3_objects(awsConfig, config)

    upload_cloudwatch_log(
        f"{config.device_model}: Data Processing is Complete!!",
        awsConfig,
        config,
    )


def main():
    parser = ArgumentParser(
        description="Get batched raw data, transform to RT Radio Messages, save"
    )
    parser.add_argument(
        "--aws-region",
        type=str,
        help="region for s3 buckets/logging, default=us-east-1",
    )
    parser.add_argument(
        "--cdf-url",
        type=str,
        help="CDF api endpoint, default=https://oo9fn5p38b.execute-api.us-east-1.amazonaws.com/Prod/",
    )
    parser.add_argument(
        "--device-model",
        type=str,
        help="allowed values: 2100, 2101, MP70",
    )
    parser.add_argument(
        "--device-operational-mode",
        type=str,
        help="allowed values: TSP, EVP",
    )
    parser.add_argument(
        "--cloudwatch-log-group",
        type=str,
        help="log group name, default=data-aggregation-Logs",
    )
    parser.add_argument(
        "--cloudwatch-log-stream-name",
        type=str,
        help="log prefix to split by device type, default={device-model}-{device-operational-mode}-logs",
    )
    parser.add_argument(
        "--incoming-bucket-name",
        type=str,
        help="source bucket, default=runtime-device-message",
    )
    parser.add_argument(
        "--outgoing-bucket-name",
        type=str,
        help="destination bucket, default=rt-radio-message",
    )
    parser.add_argument(
        "--incoming-s3-path",
        type=str,
        help="source path, default={device-model}-{device-operational-mode}",
    )
    parser.add_argument(
        "--outgoing-s3-path",
        type=str,
        help="destination path, default=root bucket folder",
    )
    parser.add_argument(
        "--source-date", type=str, help="ISO datetime-like string (ex. '2021-08-22')"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    # ToDo: use BaseSettings object instead of creating manually
    # get from command line args or environment variables
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    aws_region = args.aws_region or os.environ.get("AWS_REGION", "us-east-1")
    cdf_url = (
        args.cdf_url
        or os.environ.get("CDF_URL")
        or "https://oo9fn5p38b.execute-api.us-east-1.amazonaws.com/Prod/"
    )
    device_model = (args.device_model or os.environ.get("device_model") or "").upper()
    device_operational_mode = (
        args.device_operational_mode
        or os.environ.get("device_operational_mode")
        or ("EVP" if device_model == "2100" else "")
        or ("TSP" if device_model == "2101" else "")
    ).upper()
    cloudwatch_log_group = (
        args.cloudwatch_log_group
        or os.environ.get("CLOUDWATCH_LOG_GROUP")
        or "data-aggregation-Logs"
    )
    cloudwatch_log_stream_name = (
        args.cloudwatch_log_stream_name
        or os.environ.get("CLOUDWATCH_LOG_STREAM_NAME")
        or f"{device_model}-logs"
    )
    incoming_bucket_name = (
        args.incoming_bucket_name
        or os.environ.get("INCOMING_BUCKET_NAME")
        or "rt-radio-message"
    )
    outgoing_bucket_name = (
        args.outgoing_bucket_name
        or os.environ.get("OUTGOING_BUCKET_NAME")
        or "runtime-device-message"
    )
    incoming_s3_path = (
        args.incoming_s3_path
        or os.environ.get("INCOMING_S3_PATH")
        or f"{device_model}-{device_operational_mode}"
    )
    outgoing_s3_path = args.outgoing_s3_path or os.environ.get("OUTGOING_S3_PATH") or ""
    # unpack date into integers for y/m/d
    source_date = datetime.fromisoformat(
        args.source_date
        or os.environ.get("SOURCE_DATE")
        or datetime.utcnow().isoformat()
    ).date()

    # ensure that device model/operational_mode have been specified
    if not (device_model and device_operational_mode):
        raise ValueError(
            f"device_model and device_operational_mode should be provided either as arguments or environment variables. {device_model=}, {device_operational_mode=}"
        )

    # ensure that s3 paths have been specified
    if incoming_s3_path is None or outgoing_s3_path is None:
        raise ValueError(
            f"incoming_s3_path and outgoing_s3_path should be provided either as arguments or environment variables. {incoming_s3_path=}, {outgoing_s3_path=}"
        )

    # ensure 210x matches expected operational model
    if device_model == "2100" and device_operational_mode != "EVP":
        raise ValueError(
            f"{device_model=} should always use device_operational_mode='EVP'"
        )
    elif device_model == "2101" and device_operational_mode != "TSP":
        raise ValueError(
            f"{device_model=} should always use device_operational_mode='TSP'"
        )

    config = Config(
        aws_region,
        cdf_url,
        device_model,
        device_operational_mode,
        cloudwatch_log_group,
        cloudwatch_log_stream_name,
        incoming_bucket_name,
        outgoing_bucket_name,
        incoming_s3_path,
        outgoing_s3_path,
        source_date,
    )

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    logging.debug(config)

    write_back_to_s3(config)


if __name__ == "__main__":
    main()
