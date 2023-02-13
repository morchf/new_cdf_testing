import json
import logging
import os
from typing import Optional, Union

import boto3
import sqlalchemy
from gtt.api import http_response
from gtt.service.schedule_adherence import (
    AuroraClient,
    ScheduleAdherenceService,
    StaticGtfsService,
)
from models import GetScheduleStatusHttpRequest, UpdateScheduleStatusHttpRequest
from pydantic import parse_obj_as
from redis import Redis
from sqlalchemy.pool import NullPool

from gtt.data_model.schedule_adherence import ScheduleStatus, VehiclePosition

logging.getLogger().setLevel(logging.INFO)


redis = Redis(
    host=os.getenv("REDIS_URL"),
    port=os.getenv("REDIS_PORT"),
    db=0,
    decode_responses=True,
)

secretsmanager = boto3.client("secretsmanager")

response = secretsmanager.get_secret_value(SecretId=os.getenv("AURORA_SECRET_NAME"))
secret_dict = json.loads(response["SecretString"])

host = secret_dict["host"]
username = secret_dict["username"]
password = secret_dict["password"]
port = secret_dict["port"]

gtfs_conn = f"postgresql://{username}:{password}@{host}:{port}/gtfs"
aurora_engine = sqlalchemy.create_engine(gtfs_conn, poolclass=NullPool)

sql_client = AuroraClient(aurora_engine)
static_gtfs_service = StaticGtfsService(sql_client)
schedule_adherence_service = ScheduleAdherenceService(redis, static_gtfs_service)


def get_schedule_status(
    agency_id: str, trip_id: str, vehicle_id: str
) -> Optional[ScheduleStatus]:
    return schedule_adherence_service.get_schedule_status(
        agency_id=agency_id,
        trip_id=trip_id,
        vehicle_id=vehicle_id,
    )


def update_schedule_status(
    agency_id: str, vehicle_position: VehiclePosition
) -> Optional[ScheduleStatus]:
    return schedule_adherence_service.update_schedule_status(
        agency_id=agency_id, vehicle_position=vehicle_position
    )


@http_response
def handler(event, context):
    logging.info(f"Received {event=}, {context=}")

    request = parse_obj_as(
        Union[GetScheduleStatusHttpRequest, UpdateScheduleStatusHttpRequest], event
    )

    if type(request) == GetScheduleStatusHttpRequest:
        return get_schedule_status(
            request.query_parameters.agency_id,
            request.query_parameters.trip_id,
            request.query_parameters.vehicle_id,
        )
    if type(request) == UpdateScheduleStatusHttpRequest:
        return update_schedule_status(request.query_parameters.agency_id, request.body)

    raise ValueError(f"Invalid request type: {request}")
