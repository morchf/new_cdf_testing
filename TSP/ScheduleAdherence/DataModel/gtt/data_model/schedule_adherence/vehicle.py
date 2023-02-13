from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel


class VehiclePosition(BaseModel):
    """Minimum needed to use schedule adherence"""

    vehicle_id: str
    trip_id: str
    latitude: float
    longitude: float
    stop_id: Optional[str]
    timestamp: datetime

    class CurrentStatus(IntEnum):
        INCOMING_AT = 0
        STOPPED_AT = 1
        IN_TRANSIT_TO = 2

    current_status: Optional[CurrentStatus]

    @property
    def is_near_stop(self) -> bool:
        return self.current_status in (
            VehiclePosition.CurrentStatus.IN_TRANSIT_TO,
            VehiclePosition.CurrentStatus.STOPPED_AT,
        )


# Realtime-GTFS models


class RtGtfsVehiclePosition(VehiclePosition):
    class ScheduleRelationship(IntEnum):
        SCHEDULED = 0
        ADDED = 1
        UNSCHEDULED = 2
        CANCELED = 3

    schedule_relationship: Optional[ScheduleRelationship]


class RtGtfsTripUpdate(BaseModel):
    class StopTimeUpdate(BaseModel):
        stop_sequence: int
        stop_id: str
        arrival_delay: int
