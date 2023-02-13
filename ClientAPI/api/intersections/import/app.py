import base64
import cgi
import csv
import io
import logging
from datetime import datetime
from os import getenv
from typing import Literal, Union

import boto3
from gtt.api import http_response
from gtt.service.asset_library import AssetLibraryAPI
from models import UploadIntersectionsRequest

s3 = boto3.client("s3")
s3_bucket = getenv("S3_BUCKET", "scp-analytics-develop--assets")

asset_lib_api = AssetLibraryAPI()


def parse_form_data(body, headers):
    fp = io.BytesIO(body)
    content_type = (
        headers["Content-Type"]
        if headers.get("Content-Type")
        else headers["content-type"]
    )
    (_, pdict) = cgi.parse_header(content_type)
    if "boundary" in pdict:
        pdict["boundary"] = pdict["boundary"].encode("ascii")
    pdict["content-length"] = len(body)

    return cgi.parse_multipart(fp, pdict)


def upload_csv(
    agency_id: str,
    data: str,
    utc_date: datetime,
    extension: Union[Literal["csv"], Literal["tsv"]] = "csv",
) -> str:
    # Parse CSV or TSV
    intersections_source = csv.reader(
        io.StringIO(data), delimiter="," if extension == "csv" else "\t"
    )

    # Convert to TSV buffer
    intersections_buffer = io.StringIO()
    intersections_dest = csv.writer(
        intersections_buffer, delimiter=",", lineterminator="\n"
    )

    intersections_dest.writerows(intersections_source)

    # Save to S3 bucket partitioned by agency ID and UTC date
    utc_date = utc_date.strftime("%Y-%m-%d")
    s3_partition = (
        f"intersections/agency_id={agency_id}/utc_date={utc_date}/intersections.tsv"
    )
    s3.upload_fileobj(
        io.BytesIO(intersections_buffer.getvalue().encode()), s3_bucket, s3_partition
    )

    return s3_partition


@http_response
def handler(event, context):
    logging.info(f"Received {event=}, {context=}")

    upload_intersections_request = UploadIntersectionsRequest(**event)

    agency = asset_lib_api.get_agency(
        upload_intersections_request.query_parameters.region_name,
        upload_intersections_request.query_parameters.agency_name,
    )
    agency_id = agency.unique_id.lower()

    form_data = parse_form_data(
        base64.b64decode(upload_intersections_request.body),
        upload_intersections_request.headers,
    )

    data = form_data.get("file", [])[0].decode()
    extension = form_data.get("type", [])[0]

    if data is None:
        raise ValueError("No data passed in 'file'")

    return upload_csv(
        agency_id=agency_id,
        utc_date=upload_intersections_request.query_parameters.utc_date,
        data=data,
        extension=extension,
    )
