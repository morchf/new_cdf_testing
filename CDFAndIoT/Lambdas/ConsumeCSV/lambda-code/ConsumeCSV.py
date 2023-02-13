import boto3
import csv

s3 = boto3.resource("s3")


def determine_row_type(entities, row):
    column1 = row[0].rstrip(" ")
    column2 = row[1].rstrip(" ")

    if column1 in entities:
        if column2 == "name" or column2 == "deviceId":
            row_type = "header"
        else:
            row_type = "content"
    elif column1 == "Done":
        row_type = "done"
    else:
        row_type = "unknown"

    return row_type


def lambda_handler(event, context):

    header_row = None
    content_row = None
    entity_types = [
        "region",
        "agency",
        "vehicle",
        "phaseselector",
        "vehicleV2",
        "communicator",
        "location",
    ]

    # get inputpath passed in
    row_cnt = event["taskResult-consume-csv"]["row_count"]
    header_row_num = event["taskResult-consume-csv"]["header_row_number"]

    # Get csv from bucket
    detail = event.get("detail")

    if detail:
        rp = detail.get("requestParameters")
    else:
        raise Exception("Input data lacks detail field, cannot download CSV from S3")

    if rp:
        bucket = rp.get("bucketName")
        key = rp.get("key")

        if not bucket:
            raise Exception(
                "Input data missing S3 bucket name, cannot download CSV from S3"
            )

        if not key:
            raise Exception("Input data missing S3 key, cannot download CSV from S3")

        tmpkey = key.replace("/", "")
        download_path = f"/tmp/{tmpkey}"
        s3.Object(bucket, key).download_file(download_path)
    else:
        raise Exception(
            "Input data missing requestParameters, cannot download CSV from S3"
        )

    # Open file and read
    with open(download_path, "r") as file:
        data = csv.reader(file, dialect="excel")
        data = list(data)
        row = data[row_cnt]

        row_type = determine_row_type(entity_types, row)

        # save header row number so that it can be used later
        if row_type == "header":
            header_row_num = row_cnt
        elif row_type == "content":
            content_row = row
        elif row_type == "unknown":
            if row_cnt != 1:
                print(f"Unexpected content row {row}")

        header_row = data[header_row_num]

        # increment row count for next go around
        row_cnt += 1

        rc = {
            "row_type": row_type,
            "row_count": row_cnt,
            "header_row_number": header_row_num,
            "header": header_row,
            "row_content": content_row,
        }
        print(rc)
    return rc
