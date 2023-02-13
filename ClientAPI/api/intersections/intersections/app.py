import logging
import os

import boto3
from gtt.api import HttpRequest, http_response
from gtt.service.phase_selector import IntersectionService, PhaseSelectorService
from models import BASIC_FIELDS, CreateRequest, GetRequest
from pydantic import parse_obj_as

from gtt.data_model.intersection import Intersection

logging.getLogger().setLevel(logging.INFO)

table_name = os.environ.get("INTERSECTIONS_TABLE_NAME")
instance_ids = os.environ.get("INSTANCE_IDS").split(",")
global_vps_table = boto3.resource("dynamodb").Table(os.environ.get("VPS_TABLE_NAME"))
dynamo_table = boto3.resource("dynamodb").Table(table_name)
ssm = boto3.client("ssm")
ec2 = boto3.client("ec2")

phase_selector_service = PhaseSelectorService(
    ssm, ec2, use_public_ip_addresses=os.environ.get("USE_PUBLIC_IPS") is not None
)
intersection_service = IntersectionService(dynamo_table, phase_selector_service)


@http_response
def handler(event, context):
    logging.info(f"Received {event=}, {context=}")

    http_request = HttpRequest(**event)
    agency_id = event["queryStringParameters"]["agencyId"].lower()
    if http_request.http_method == "GET":
        """TODO: Improve the GET response time when we have more than around 10 V764s associated to an agency.
        Below are few options that were discussed:
            1.  Adding a refresh button on the UI to update the dynamodb table.
        """
        parse_obj_as(GetRequest, http_request)
        return [
            intersection.dict(by_alias=True, include=BASIC_FIELDS)
            for intersection in intersection_service.list(
                agency_id=agency_id, include_not_configured=True
            )
        ]

    if http_request.http_method == "POST":
        create_request = parse_obj_as(CreateRequest, http_request)

        # Use any unconfigured serial number
        unconfigured_intersection = intersection_service.get_not_configured(agency_id)

        if unconfigured_intersection is None:
            raise Exception("No unconfigured intersections available")

        connection = phase_selector_service.get_connection(
            instance_ids, unconfigured_intersection.serial_number
        )

        if connection is None:
            raise Exception(
                f"No matching connection details for serial number: {unconfigured_intersection.serial_number}"
            )

        ip_address, port = connection
        logging.info(
            f"Using device with SN={unconfigured_intersection.serial_number} at {ip_address}:{port}"
        )
        intersection = Intersection(
            agency_id=agency_id,
            serial_number=unconfigured_intersection.serial_number,
            ip_address=ip_address,
            port=port,
            **create_request.body,
        )
        new_intersection = intersection_service.write(intersection)

        if new_intersection is None:
            return None

        return new_intersection.dict(
            by_alias=True,
            include={
                *BASIC_FIELDS,
                "approach_map",
                "outputs",
                "thresholds",
            },
        )

    raise ValueError(f"Invalid request type: {http_request}")
