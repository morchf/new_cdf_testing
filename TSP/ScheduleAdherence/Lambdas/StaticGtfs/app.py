import logging
import os
from typing import Union

from gtt.api import http_response
from models import InvalidateStaticGtfsEventRequest, InvalidateStaticGtfsHttpRequest
from pydantic import parse_obj_as
from redis import Redis

from gtt.data_model.schedule_adherence.static_gtfs import StaticGtfsChannel

logging.getLogger().setLevel(logging.INFO)


redis = Redis(
    host=os.getenv("REDIS_URL"),
    port=os.getenv("REDIS_PORT"),
    db=0,
    decode_responses=True,
)


def invalidate_static_gtfs(agecy_id: str):
    invalidate_channel = StaticGtfsChannel.invalidate(agency_id=agecy_id)
    logging.info(f"Invalidating static GTFS on channel {invalidate_channel}")
    return redis.publish(invalidate_channel, "")


@http_response
def handler(event, context):
    logging.info(f"Received {event=}, {context=}")

    request = parse_obj_as(
        Union[InvalidateStaticGtfsEventRequest, InvalidateStaticGtfsHttpRequest], event
    )

    if type(request) == InvalidateStaticGtfsHttpRequest:
        return invalidate_static_gtfs(request.query_parameters.agency_id)
    if type(request) == InvalidateStaticGtfsEventRequest:
        return invalidate_static_gtfs(request.detail.agency_id)

    raise ValueError(f"Invalid request type: {request}")
