from collections import defaultdict
import boto3
import pandas as pd
import io
import json
import datetime
import os

DEVICECONFIG_PATH = "/CMS/DEVICECONFIGURATION/PARTITION/date_ran="
DEVICE_PATH = "/CMS/DEVICE/PARTITION/date_ran="

# Using an environment varibale env to get the environment information
env = os.environ["Env"]
GTT_ETL_BUCKET = "backup-gtt-etl-data-" + env
FIRM_VER_BUCKET = "firmware-history-" + env
FILE_NAME = (
    "date_ran="
    + datetime.datetime.now().strftime("%Y-%m-%d")
    + "/firmware_version_and_date.json"
)


def lambda_handler(event, context):
    """Retreives the data from Device table and stores it in firmware-history-dev bucket"""
    try:
        # For getting the login info from the session
        session = boto3.Session()
        client = session.client("s3")

        # get the list of agency ids
        agencies = []
        obj_list = client.list_objects(Bucket=GTT_ETL_BUCKET)
        for i in obj_list["Contents"]:
            aid = str(i["Key"]).split("/")[0]
            if aid not in agencies:
                agencies.append(aid)

        for agency_id in agencies:
            DEVICE_PREFIX = agency_id + DEVICE_PATH
            DEVICE_CONF_PREFIX = agency_id + DEVICECONFIG_PATH
            # get the latest data (based on date_ran)
            paginator = client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=GTT_ETL_BUCKET,
                # Prefix=agency_id + "/CMS/DEVICE/PARTITION/",
                Prefix=DEVICE_PREFIX,
            )

            latest_date_ran = None
            for bucket in page_iterator:
                for file in bucket["Contents"]:
                    if "date_ran" in str(file["Key"]):
                        date_ran = str(file["Key"]).split("/")[-2].split("=")[1]
                        if latest_date_ran is None or date_ran > latest_date_ran:
                            latest_date_ran = date_ran

            # Reading the "Device" table data from the most recent date_run
            apks = client.list_objects(
                Bucket=GTT_ETL_BUCKET,
                Prefix=DEVICE_PREFIX + latest_date_ran + "/",
            )

            frames = []
            for i in apks["Contents"]:
                obj = client.get_object(Bucket=GTT_ETL_BUCKET, Key=i["Key"])
                # read all the parquet files and append it to a list
                frames.append(
                    pd.read_parquet(io.BytesIO(obj["Body"].read()), engine="auto")[
                        ["DeviceId", "DeviceSerialNumber", "Revision68HC11"]
                    ]
                )
            # Concatenating all the data into a single pandas data frame
            device_dataframe = pd.concat(frames)
            # Read "DeviceConfiguration" table data
            latest_date_ran = None
            for bucket in page_iterator:
                for file in bucket["Contents"]:
                    if "date_ran" in str(file["Key"]):
                        date_ran = str(file["Key"]).split("/")[-2].split("=")[1]
                        if latest_date_ran is None or date_ran > latest_date_ran:
                            latest_date_ran = date_ran
            apks = client.list_objects(
                Bucket=GTT_ETL_BUCKET,
                Prefix=DEVICE_CONF_PREFIX + latest_date_ran + "/",
            )

            frames = []
            # Read all the parquet files and store only the "DeviceID" along with the "CreationDateTime"
            for i in apks["Contents"]:
                obj = client.get_object(Bucket=GTT_ETL_BUCKET, Key=i["Key"])
                frames.append(
                    pd.read_parquet(io.BytesIO(obj["Body"].read()), engine="auto")[
                        ["DeviceId", "CreatedDateTime"]
                    ]
                )
            # Same as above merge all the data frames
            device_configuration_df = pd.concat(frames)
            frames.clear()
            # Merge the two dataframes on "DeviceID" as the key
            version_date_df = pd.merge(
                device_dataframe, device_configuration_df, on=["DeviceId"]
            )

            # save the data as a dictionary with "DeviceSerialNumber" as the key
            serial_number_dict = defaultdict(list)
            for idx, row in version_date_df.iterrows():
                timestamp_dict = row.to_dict()
                update_version_info_flag = False
                if timestamp_dict["DeviceSerialNumber"] not in serial_number_dict:
                    # For each key create a nested dictionary with "Revision68HC11" (Firmware version) as the key
                    serial_number_dict[timestamp_dict["DeviceSerialNumber"]] = {}
                    update_version_info_flag = True
                else:
                    # If there is already "DeviceSerialNumber" stored as a key check for the firmware version
                    if (
                        timestamp_dict["Revision68HC11"]
                        in serial_number_dict[timestamp_dict["DeviceSerialNumber"]]
                    ):
                        # if the same firmware version is present then check if there is the oldest date
                        if serial_number_dict[timestamp_dict["DeviceSerialNumber"]][
                            timestamp_dict["Revision68HC11"]
                        ] > timestamp_dict["CreatedDateTime"].strftime(
                            "%Y %m %d %H %M %S"
                        ):
                            update_version_info_flag = True
                    else:
                        update_version_info_flag = True
                # Update "serial_number_dict" dictionary with the version history and date
                if update_version_info_flag:
                    serial_number_dict[timestamp_dict["DeviceSerialNumber"]][
                        timestamp_dict["Revision68HC11"]
                    ] = timestamp_dict["CreatedDateTime"].strftime("%Y %m %d %H %M %S")
            # Convert it into json data
            json_data = json.dumps(serial_number_dict).encode("UTF-8")
            upload_bytestream = bytes(json_data)
            # store it in the bucket 'firmware-history-'+env
            # Specify the file name that will be written to S3 bucket
            tagging = "uploaded_datetime=" + datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            client.put_object(
                Bucket=FIRM_VER_BUCKET,
                Key=FILE_NAME,
                Body=upload_bytestream,
                Tagging=tagging,
            )

        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName="UpdateFirmwareVersionToElasticache",
            InvocationType="Event",
            LogType="None",
            Qualifier="$LATEST",
        )
        return 200

    except Exception as e:
        print("There is an exeption while executing lambda")
        print(e)
