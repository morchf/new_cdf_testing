import logging
import os

import boto3
from gtt.api import HttpRequest, http_response
from gtt.service.phase_selector import IntersectionService, PhaseSelectorService
from models import BASIC_FIELDS, CreateRequest, GetRequest, UpdateRequest
from pydantic import parse_obj_as

from gtt.data_model.intersection import Intersection

logging.getLogger().setLevel(logging.INFO)

table_name = os.environ.get("INTERSECTIONS_TABLE_NAME")
dynamo_table = boto3.resource("dynamodb").Table(table_name)
global_vps_table = boto3.resource("dynamodb").Table(os.environ.get("VPS_TABLE_NAME"))
ssm = boto3.client("ssm")
ec2 = boto3.client("ec2")

phase_selector_service = PhaseSelectorService(ssm, ec2)
intersection_service = IntersectionService(dynamo_table, phase_selector_service)


@http_response
def handler(event, context):
    logging.info(f"Received {event=}, {context=}")

    http_request = HttpRequest(**event)
    agency_id = event["queryStringParameters"]["agencyId"].lower()
    if http_request.http_method == "GET":
        get_request = parse_obj_as(GetRequest, http_request)

        intersection = intersection_service.read(
            agency_id=agency_id,
            serial_number=get_request.path_parameters.serial_number,
        )

        if intersection is None:
            return None

        return intersection.dict(
            by_alias=True,
            include={
                *BASIC_FIELDS,
                "approach_map",
                "outputs",
                "thresholds",
            },
        )

    if http_request.http_method == "POST":
        create_request = parse_obj_as(CreateRequest, http_request)

        intersection = Intersection(
            serial_number=create_request.query_parameters.serial_number,
            **create_request.body,
        )
        new_intersection = intersection_service.create(intersection)

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

    if http_request.http_method == "PUT":
        create_request = parse_obj_as(UpdateRequest, http_request)

        intersection = Intersection(
            agency_id=agency_id,
            serial_number=create_request.path_parameters.serial_number,
            **create_request.body,
        )
        updated_intersection = intersection_service.write(intersection)

        if updated_intersection is None:
            return None

        return updated_intersection.dict(
            by_alias=True,
            include={
                *BASIC_FIELDS,
                "approach_map",
                "outputs",
                "thresholds",
            },
        )

    raise ValueError(f"Invalid request type: {http_request}")
