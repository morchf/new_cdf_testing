import logging
import math
from datetime import datetime, time, timedelta
from typing import Dict, ForwardRef, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, PrivateAttr, parse_obj_as, validator
from pydantic.types import NonNegativeInt

from .redis import RedisChannel
from .static_gtfs import StaticGtfsStop, StaticGtfsStopTime
from .vehicle import VehiclePosition

ScheduleStatus = ForwardRef("ScheduleStatus")


def geodistance(lat1, lon1, lat2, lon2):
    """Geodistance in meters between two coordinates"""
    return (
        math.asin(
            math.sqrt(
                math.sin(math.radians(lat2 - lat1) / 2) ** 2
                + math.sin(math.radians(lon2 - lon1) / 2) ** 2
                * math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
            )
        )
        * 7926.3352
    )


def seconds_diff(
    t1: Union[datetime, time],
    t2: Union[datetime, time],
    *args,
    **kwargs,
) -> int:
    """Difference in seconds between timestamps/times

    Assume the times cross midnight if the time difference is greater than 12
    hours and one or more of the times exclude the date

    Args:
        t1 (str): Timestamp or time
        t2 (str): Timestamp or time

    Returns:
        int: Seconds difference
    """
    # Both 'datetime'
    if isinstance(t1, datetime) and isinstance(t2, datetime):
        return (t1 - t2).total_seconds()

    if isinstance(t1, time) and isinstance(t2, time):
        t1 = datetime.combine(datetime.fromtimestamp(0), t1)
        t2 = datetime.combine(datetime.fromtimestamp(0), t2)
    else:
        if isinstance(t1, time):
            t1 = datetime.combine(t2.date(), t1)

        if isinstance(t2, time):
            t2 = datetime.combine(t1.date(), t2)

    diff = t1 - t2

    if diff > timedelta(hours=12):
        return (diff - timedelta(days=1)).total_seconds()
    if diff < timedelta(hours=-12):
        return (diff + timedelta(days=1)).total_seconds()

    return diff.total_seconds()


class StopEvent(BaseModel):
    stop_id: str
    timestamp: datetime

    @classmethod
    def is_valid(
        cls, vehicle_position: VehiclePosition, stop: Optional[StaticGtfsStop]
    ):
        if stop is None:
            return False

        return (
            geodistance(
                stop.stop_lat,
                stop.stop_lon,
                vehicle_position.latitude,
                vehicle_position.longitude,
            )
            < 30
        )


class Schedule(BaseModel, underscore_attrs_are_private=True):
    # Sorted by stop sequence / stop time
    stop_times: List[StaticGtfsStopTime]

    _stop_times_by_stop: Optional[Dict[str, StaticGtfsStopTime]] = PrivateAttr(
        default=None
    )
    _stop_times_by_sequence: Optional[
        Dict[NonNegativeInt, Tuple[NonNegativeInt, StaticGtfsStopTime]]
    ] = PrivateAttr(default=None)

    @validator("stop_times")
    def non_empty_stop_times(cls, v):
        if v is None or len(v) == 0:
            raise ValueError("Empty stop times")

        return list(sorted(v, key=lambda x: x.stop_sequence))

    @property
    def stop_times_by_stop(self) -> Dict[int, StaticGtfsStopTime]:
        """Lazy-loaded stop lookup"""
        if self._stop_times_by_stop is None:
            self._stop_times_by_stop = {
                stop_time.stop.stop_id: stop_time
                for stop_time in self.stop_times
                if stop_time.stop is not None
            }
        return self._stop_times_by_stop

    @property
    def stop_times_by_sequence(self) -> Dict[int, Tuple[int, StaticGtfsStopTime]]:
        """Lazy-loaded sequence lookup with indexing based on stop sequence

        Sequence does not always start at 0/1 and may skip values
        """
        if self._stop_times_by_sequence is None:
            self._stop_times_by_sequence = {
                stop_time.stop_sequence: (index, stop_time)
                for index, stop_time in enumerate(self.stop_times)
            }
        return self._stop_times_by_sequence

    @property
    def stops(self) -> List[StaticGtfsStop]:
        return parse_obj_as(
            List[StaticGtfsStop],
            [
                stop_time.stop
                for stop_time in self.stop_times
                if stop_time.stop is not None
            ],
        )

    def get_stop_time(
        self, stop_id: Optional[str] = None, stop_sequence: Optional[int] = None
    ) -> Optional[StaticGtfsStopTime]:
        """Get stop time by sequence or ID, sequence taking precendence

        Args:
            stop_id (Optional[str], optional): Stop ID. Defaults to None.
            stop_sequence (Optional[int], optional): Stop sequence. Defaults to None.

        Returns:
            Optional[StaticGtfsStopTime]: Stop time
        """
        if stop_sequence is not None:
            (_, stop) = self.stop_times_by_sequence.get(stop_sequence)
            return stop

        if stop_id is None:
            return None

        return self.stop_times_by_stop.get(stop_id)

    def get_next_stop_time(
        self, stop_id: Optional[str] = None, stop_sequence: Optional[int] = None
    ) -> Optional[StaticGtfsStopTime]:
        """Get next stop time by sequence or ID, sequence taking precendence

        Args:
            stop_id (Optional[str], optional): Stop ID. Defaults to None.
            stop_sequence (Optional[int], optional): Stop sequence. Defaults to None.

        Returns:
            Optional[StaticGtfsStopTime]: Stop time
        """
        current_stop_time = self.get_stop_time(
            stop_id=stop_id, stop_sequence=stop_sequence
        )

        if current_stop_time is None:
            return None

        # Can't assume stop sequences are in-order starting at 0/1
        # Must use ordered list to find next stop
        (current_stop_index, _) = self.stop_times_by_sequence.get(
            current_stop_time.stop_sequence
        )
        next_stop_index = current_stop_index + 1

        if next_stop_index >= len(self.stop_times):
            return None

        return self.stop_times[next_stop_index]

    def closest_stop_time(
        self,
        vehicle_position: VehiclePosition,
        schedule_status: Optional[ScheduleStatus] = None,
    ) -> Optional[StaticGtfsStopTime]:
        # Use existing schedule status to exclude visited stops
        stop_times = (
            self.stop_times
            if schedule_status is None
            else self.unvisited_stop_times(schedule_status)
        )

        if len(stop_times) == 0:
            return None

        return min(
            stop_times,
            key=lambda x: math.inf
            if x.stop is None
            else geodistance(
                x.stop.stop_lat,
                x.stop.stop_lon,
                vehicle_position.latitude,
                vehicle_position.longitude,
            ),
            default=None,
        )

    def unvisited_stop_times(
        self, schedule_status: ScheduleStatus
    ) -> List[StaticGtfsStopTime]:
        if len(schedule_status.stop_events) <= 0:
            return self.stop_times

        visited_stop_ids = list(map(lambda x: x.stop_id, schedule_status.stop_events))

        return [
            stop_time
            for stop_time in self.stop_times
            if stop_time.stop is not None and stop_time.stop_id not in visited_stop_ids
        ]


class ScheduleStatus(BaseModel):
    trip_id: str
    vehicle_id: str
    delay: float
    last_updated: Optional[datetime]
    next_update: Optional[datetime] = None
    next_stop: Optional[StaticGtfsStop] = None
    exact: Optional[bool] = False
    stop_events: Optional[List[StopEvent]] = Field(default_factory=list)

    def equals(self, other_schedule_status: "ScheduleStatus"):
        return self.delay == other_schedule_status.delay

    def late(self, buffer: Optional[int] = 0) -> bool:
        """Current vehicle is late

        Args:
            buffer (Optional[int], optional): Allowable band where vehicle is not late. Defaults to 0.

        Returns:
            bool: Whether vehicle is late
        """
        return (self.delay - buffer) > 0

    def early(self, buffer: Optional[int] = 0) -> bool:
        """Current vehicle is early

        Args:
            buffer (Optional[int], optional): Allowable band where vehicle is not early. Defaults to 0.

        Returns:
            bool: Whether vehicle is late
        """
        return (self.delay + buffer) < 0

    def to_string(self):
        return f"""Delay: {str(self.delay * -1) + 's Early' if self.delay < 0 else str(self.delay) + 's Late'}
Last Updated: {self.last_updated}
Next Update: {self.next_update}
Number of Stop Events: {0 if self.stop_events is None else len(self.stop_events)}
Latest Stop ID: {None if self.latest_stop_event is None else self.latest_stop_event.stop_id}
Next Stop ID: {None if self.next_stop is None else self.next_stop.stop_id}"""

    @property
    def latest_stop_event(self) -> Optional[StopEvent]:
        if self.stop_events is None or len(self.stop_events) <= 0:
            return None

        return self.stop_events[-1]

    @classmethod
    def new(
        cls,
        delay: float,
        stop_events: Optional[List[StopEvent]] = None,
        schedule: Optional[Schedule] = None,
        **kwargs,
    ) -> Optional[ScheduleStatus]:
        last_updated = datetime.now()

        if schedule is None or stop_events is None or len(stop_events) <= 0:
            return cls(
                delay=delay,
                last_updated=last_updated,
                stop_events=stop_events,
                **kwargs,
            )

        latest_stop_event = stop_events[-1]
        current_stop_time = schedule.get_stop_time(latest_stop_event.stop_id)
        next_stop_time = schedule.get_next_stop_time(latest_stop_event.stop_id)

        next_stop = None
        next_update = None

        if next_stop_time is not None and next_stop_time.stop is not None:
            next_stop = next_stop_time.stop

        if (
            next_stop is not None
            and current_stop_time is not None
            and (
                current_stop_time.departure_time is not None
                or current_stop_time.arrival_time is not None
            )
            and next_stop_time.arrival_time is not None
        ):
            next_update = latest_stop_event.timestamp + timedelta(
                seconds=seconds_diff(
                    next_stop_time.arrival_time,
                    # May not have explicit departure time
                    current_stop_time.departure_time or current_stop_time.arrival_time,
                )
            )

        return cls(
            delay=delay,
            last_updated=last_updated,
            stop_events=stop_events,
            next_stop=next_stop,
            next_update=next_update,
            **kwargs,
        )

    @classmethod
    def from_schedule(
        cls, schedule: Schedule, vehicle_position: VehiclePosition
    ) -> Optional[ScheduleStatus]:
        """Calculate schedule status from schedule and vehicle position

        Args:
            schedule (StaticGtfsSchedule): Static GTFS schedule with stop locations
            vehicle_position (VehiclePosition): Current vehicle position

        Returns:
            ScheduleStatus: New schedule status
        """
        stop_time = None

        # Match to next stop
        if vehicle_position.stop_id is not None and vehicle_position.is_near_stop:
            stop_time = schedule.get_stop_time(vehicle_position.stop_id)

        # Match to closest stop, allowing new or last stop
        if stop_time is None or not StopEvent.is_valid(
            vehicle_position, stop_time.stop
        ):
            stop_time = schedule.closest_stop_time(vehicle_position)

        if stop_time is None:
            return None

        # Use arrival time to compare current timestamp
        delay = seconds_diff(vehicle_position.timestamp, stop_time.arrival_time)

        return cls.new(
            vehicle_id=vehicle_position.vehicle_id,
            trip_id=vehicle_position.trip_id,
            delay=delay,
            exact=stop_time.timepoint == StaticGtfsStopTime.Timepoint.EXACT,
            stop_events=[
                StopEvent(
                    stop_id=stop_time.stop_id, timestamp=vehicle_position.timestamp
                ),
            ],
            schedule=schedule,
        )

    @classmethod
    def from_schedule_status(
        cls,
        schedule: Schedule,
        vehicle_position: VehiclePosition,
        schedule_status: Optional[ScheduleStatus] = None,
    ) -> Optional[ScheduleStatus]:
        """Calculate schedule status from schedule, vehicle position, and current schedule status

        Args:
            schedule (StaticGtfsSchedule): Static GTFS schedule with stop locations
            vehicle_position (VehiclePosition): Current vehicle position
            schedule_status (Optional[ScheduleStatus], optional): Current schedule status. Defaults to None.

        Returns:
            ScheduleStatus: New schedule status
        """
        if schedule_status is None:
            logging.debug("No cached schedule status")
            return cls.from_schedule(schedule, vehicle_position)

        stop_time = None

        # Match to next stop
        next_stop_id = (
            vehicle_position.stop_id
            if vehicle_position.stop_id is not None and vehicle_position.is_near_stop
            else None
        )

        # Use last stop event
        if next_stop_id is None and len(schedule_status.stop_events) > 0:
            last_stop_id = schedule_status.stop_events[-1].stop_id
            next_stop = schedule.get_next_stop_time(last_stop_id)

            if next_stop is not None:
                next_stop_id = next_stop.stop_id

        # Get expected stop
        if next_stop_id:
            stop_time = schedule.get_stop_time(next_stop_id)

        # Match to closest stop, if better
        if stop_time is None or not StopEvent.is_valid(
            vehicle_position, stop_time.stop
        ):
            logging.debug("Looking for closest stop")
            closest_stop_time_time = schedule.closest_stop_time(
                vehicle_position, schedule_status
            )

            if closest_stop_time_time and StopEvent.is_valid(
                vehicle_position, closest_stop_time_time.stop
            ):
                logging.debug(f"Closest stop ID: {closest_stop_time_time.stop.stop_id}")
                stop_time = closest_stop_time_time

        logging.debug(f"Using stop ID: {stop_time.stop_id if stop_time else None}")

        if stop_time is None:
            return None

        # Use arrival time to compare current timestamp
        logging.debug(
            f"Calculating delay between {vehicle_position.timestamp} and {stop_time.arrival_time}"
        )
        delay = seconds_diff(vehicle_position.timestamp, stop_time.arrival_time)

        # Attach existing stop events
        return cls.new(
            vehicle_id=vehicle_position.vehicle_id,
            trip_id=vehicle_position.trip_id,
            delay=delay,
            exact=stop_time.timepoint == StaticGtfsStopTime.Timepoint.EXACT,
            stop_events=[
                *schedule_status.stop_events,
                StopEvent(
                    stop_id=stop_time.stop_id, timestamp=vehicle_position.timestamp
                ),
            ],
            schedule=schedule,
        )

    @classmethod
    def from_headway(
        cls,
        schedule: Schedule,
        vehicle_position: VehiclePosition,
        headway: int,
        other_vehicle_statuses: List[ScheduleStatus],
        schedule_status: Optional[ScheduleStatus] = None,
    ) -> Optional[ScheduleStatus]:
        raise NotImplementedError()


# Redis Channels


class ScheduleAdherenceChannel(RedisChannel):
    channel_namespace = "tsp_in_cloud"
    channel_format = "trip_delay:{agency_id}:{trip_id}:{vehicle_id}"
