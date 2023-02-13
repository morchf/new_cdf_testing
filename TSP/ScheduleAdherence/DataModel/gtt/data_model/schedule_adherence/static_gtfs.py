from datetime import time
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, validator
from pydantic.types import NonNegativeInt, confloat

from gtt.data_model.schedule_adherence import RedisChannel


class StaticGtfsStop(BaseModel):
    stop_id: str
    stop_name: Optional[str]
    stop_lat: confloat(ge=-90, le=90)
    stop_lon: confloat(ge=-180, le=180)

    # Unused
    # stop_code: Optional[str]
    # tts_stop_name: Optional[str]
    # stop_desc: Optional[str]
    # zone_id: Optional[str]
    # stop_url: Optional[str]
    # location_type: Optional[str]
    # parent_station: Optional[str]
    # stop_timezone: Optional[str]
    # wheelchair_boarding: Optional[str]
    # level_id: Optional[str]
    # platform_code: Optional[str]

    @validator("stop_name")
    def trim_stop_name(cls, v):
        return v.strip() if v else v


class StaticGtfsStopTime(BaseModel, validate_assignment=True, use_enum_values=True):
    trip_id: str
    stop_id: str
    stop_sequence: NonNegativeInt
    arrival_time: Optional[time]
    departure_time: Optional[time]

    # Unused
    stop_headsign: Optional[str]
    pickup_type: Optional[str]
    drop_off_type: Optional[str]
    continuous_pickup: Optional[str]
    continuous_drop_off: Optional[str]
    shape_dist_traveled: Optional[str]

    class Timepoint(IntEnum):
        APPROXIMATE = 0
        EXACT = 1

    timepoint: Timepoint = Timepoint.EXACT

    @validator("timepoint", pre=True)
    def set_timepoint(cls, v):
        return v or StaticGtfsStopTime.Timepoint.EXACT

    stop: Optional[StaticGtfsStop]


class StaticGtfsTrip(BaseModel):
    route_id: Optional[str]
    service_id: Optional[str]
    trip_id: str
    trip_headsign: Optional[str]
    trip_short_name: Optional[str]
    direction_id: Optional[str]
    block_id: Optional[str]
    shape_id: Optional[str]
    wheelchair_accessible: Optional[str]
    bikes_allowed: Optional[str]

    class Stop(BaseModel):
        id: str

    stops: Optional[List[Stop]]


# Redis Channels


class StaticGtfsChannel(RedisChannel):
    channel_namespace = "tsp_in_cloud"
    channel_format = "static_gtfs:{agency_id}:all:{trip_id}"

    @classmethod
    def invalidate(cls, **kwargs):
        return cls.channel(channel_prefix="invalidate", channel_kwargs=kwargs)


class StaticGtfsStopTimesChannel(RedisChannel):
    channel_namespace = "tsp_in_cloud"
    channel_format = "static_gtfs:{agency_id}:stop_times:{trip_id}"
