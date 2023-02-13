import logging
from typing import Dict, List, Optional

from pydantic import parse_raw_as
from redis import Redis

from gtt.data_model.schedule_adherence import (
    Schedule,
    ScheduleAdherenceChannel,
    ScheduleStatus,
    StaticGtfsStopTime,
    VehiclePosition,
)
from gtt.data_model.schedule_adherence.static_gtfs import StaticGtfsStopTimesChannel

from .static_gtfs.static_gtfs_service import StaticGtfsService


class StaticGtfsStops:
    """Utility to keep track of static GTFS stop coordinates"""

    stop_times: List[StaticGtfsStopTime]
    _points: Optional[bytes] = None

    @property
    def points(self) -> bytes:
        return self._points or b""


class StaticGtfsCache:
    _redis: Redis
    _schedule_cache: Dict[str, str]
    _static_gtfs_service: StaticGtfsService

    def __init__(self, redis: Redis, static_gtfs_service: StaticGtfsService):
        self._redis = redis
        self._static_gtfs_service = static_gtfs_service

        self._schedule_cache = {}

    def set_schedule(
        self, agency_id: str, trip_id: str, schedule: Schedule
    ) -> Schedule:
        # Update Redis cache
        self._redis.set(
            StaticGtfsStopTimesChannel.cache(agency_id=agency_id, trip_id=trip_id),
            schedule.json(),
        )

        # Save to local cache
        agency_schedule_cache = self._schedule_cache.get(agency_id)
        if agency_schedule_cache is None:
            agency_schedule_cache = {}
            self._schedule_cache[agency_id] = agency_schedule_cache

        agency_schedule_cache[trip_id] = schedule

    def get_schedule(self, agency_id: str, trip_id: str) -> Optional[Schedule]:
        # Pull directly from local cache
        local_schedule = self._schedule_cache.get(agency_id, {}).get(trip_id)
        if local_schedule is not None:
            return local_schedule

        # Convert Redis string to bytes object
        redis_schedule = self._redis.get(
            StaticGtfsStopTimesChannel.cache(agency_id=agency_id, trip_id=trip_id),
        )
        if redis_schedule is not None:
            try:
                schedule = parse_raw_as(Schedule, redis_schedule)
                self.set_schedule(
                    agency_id=agency_id,
                    trip_id=trip_id,
                    schedule=schedule,
                )
                return schedule
            except ValueError:
                logging.error("Invalid schedule in cache")
                self.remove_schedule(agency_id=agency_id, trip_id=trip_id)

        stop_times = self._static_gtfs_service.get_stop_times(
            agency_id=agency_id, trip_id=trip_id
        )

        if not stop_times:
            logging.error(f"No stop times available for trip: {agency_id=}, {trip_id=}")
            return None

        try:
            schedule = Schedule(stop_times=stop_times)
        except ValueError:
            logging.error("Invalid schedule")
            return None

        self.set_schedule(agency_id=agency_id, trip_id=trip_id, schedule=schedule)

        return schedule

    def remove_schedule(self, agency_id: str, trip_id: str):
        self._redis.delete(
            StaticGtfsStopTimesChannel.cache(agency_id=agency_id, trip_id=trip_id),
        )

    def clear(self, agency_id: str):
        if agency_id in self._schedule_cache:
            self._schedule_cache.pop(agency_id)

        for key in self._redis.scan_iter(
            StaticGtfsStopTimesChannel.cache(agency_id=agency_id)
        ):
            self._redis.delete(key)


class ScheduleAdherenceService:
    _redis: Redis
    _static_gtfs_service: StaticGtfsService
    _static_gtfs_cache: StaticGtfsCache

    def __init__(self, redis: Redis, static_gtfs_service: StaticGtfsService):
        self._redis = redis
        self._static_gtfs_service = static_gtfs_service
        self._static_gtfs_cache = StaticGtfsCache(redis, static_gtfs_service)

    def update_schedule_status(
        self, agency_id: str, vehicle_position: VehiclePosition
    ) -> Optional[ScheduleStatus]:
        """Update the schedule status for a vehicle

        Args:
            agency_id (str): Agency GUID
            vehicle_position (VehiclePosition): Vehicle position

        Returns:
            Optional[ScheduleStatus]: New schedule status, if values have changed
        """
        current_schedule_status = self.get_schedule_status(
            agency_id, vehicle_position.trip_id, vehicle_position.vehicle_id
        )
        new_schedule_status = self._calculate_schedule_status(
            agency_id, vehicle_position, current_schedule_status
        )

        # Compare cached value to new value
        if new_schedule_status is None or (
            current_schedule_status is not None
            and current_schedule_status.equals(new_schedule_status)
        ):
            return

        self.set_schedule_status(agency_id, vehicle_position, new_schedule_status)

        return new_schedule_status

    def _calculate_schedule_status(
        self,
        agency_id: str,
        vehicle_position: VehiclePosition,
        schedule_status: Optional[ScheduleStatus] = None,
    ) -> Optional[ScheduleStatus]:
        schedule = self._static_gtfs_cache.get_schedule(
            agency_id, vehicle_position.trip_id
        )

        if schedule is None:
            return None

        logging.debug(
            f"Calculating schedule status: {agency_id=}, vehicle_id={vehicle_position.vehicle_id}, existing={schedule_status is not None}"
        )
        return ScheduleStatus.from_schedule_status(
            schedule, vehicle_position, schedule_status
        )

    def get_schedule_status(
        self, agency_id: str, trip_id: str, vehicle_id: str
    ) -> Optional[ScheduleStatus]:
        """Get cached schedule status

        Args:
            agency_id (str): Agency GUID
            trip_id (str): Trip ID
            vehicle_id (str): Vehicle ID

        Returns:
            Optional[ScheduleStatus]: Schedule status
        """
        cached_schedule_status = self._redis.get(
            ScheduleAdherenceChannel.cache(
                agency_id=agency_id, trip_id=trip_id, vehicle_id=vehicle_id
            )
        )

        if cached_schedule_status is None:
            return None

        try:
            return ScheduleStatus.parse_raw(cached_schedule_status)
        except ValueError as e:
            logging.error(f"Invalid status in cache: {e}")
            return None

    def set_schedule_status(
        self,
        agency_id: str,
        vehicle_position: VehiclePosition,
        schedule_status: ScheduleStatus,
    ) -> ScheduleStatus:
        # Update cache entry and publish notification
        self._redis.set(
            ScheduleAdherenceChannel.cache(
                agency_id=agency_id,
                trip_id=vehicle_position.trip_id,
                vehicle_id=vehicle_position.vehicle_id,
            ),
            schedule_status.json(),
        )
        self._redis.publish(
            ScheduleAdherenceChannel.new(
                agency_id=agency_id,
                trip_id=vehicle_position.trip_id,
                vehicle_id=vehicle_position.vehicle_id,
            ),
            schedule_status.json(),
        )

        return schedule_status

    def clear_schedule_status(self, agency_id: str):
        for key in self._redis.scan_iter(
            ScheduleAdherenceChannel.cache(agency_id=agency_id)
        ):
            self._redis.delete(key)

    def invalidate(self, agency_id: str):
        # Remove any cached static GTFS calues
        self._static_gtfs_cache.clear(agency_id)

        # TODO: Recalculate existing trip delay now or for every vehicle on next call?
        self.clear_schedule_status(agency_id)
