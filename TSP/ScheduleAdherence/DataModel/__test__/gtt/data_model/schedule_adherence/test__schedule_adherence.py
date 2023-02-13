from datetime import datetime, time, timedelta
from typing import List

import pytest
from pydantic import parse_obj_as

from gtt.data_model.schedule_adherence import (
    Schedule,
    ScheduleStatus,
    StaticGtfsStop,
    StaticGtfsStopTime,
    StopEvent,
    VehiclePosition,
)
from gtt.data_model.schedule_adherence.schedule_adherence import seconds_diff


class TestScheduleAdherence:
    def test__seconds_diff__basic(self):
        dt1 = datetime.strptime("2022-09-01 12:05:06", "%Y-%m-%d %H:%M:%S")
        dt2 = datetime.strptime("2022-09-01 12:05:08", "%Y-%m-%d %H:%M:%S")

        t1 = time(12, 5, 6)
        t2 = time(12, 5, 8)

        assert seconds_diff(dt1, dt2) == -2.0
        assert seconds_diff(dt1, t2) == -2.0
        assert seconds_diff(t1, dt2) == -2.0
        assert seconds_diff(t1, t2) == -2.0

        # Swap
        dt1, dt2 = dt2, dt1
        t1, t2 = t2, t1

        assert seconds_diff(dt1, dt2) == 2.0
        assert seconds_diff(dt1, t2) == 2.0
        assert seconds_diff(t1, dt2) == 2.0
        assert seconds_diff(t1, t2) == 2.0

    def test__seconds_diff__across_midnight(self):
        dt1 = datetime.strptime("2022-10-03 23:59:59", "%Y-%m-%d %H:%M:%S")
        dt2 = datetime.strptime("2022-10-04 00:00:01", "%Y-%m-%d %H:%M:%S")

        t1 = time(23, 59, 59)
        t2 = time(0, 0, 1)

        assert seconds_diff(dt1, dt2) == -2.0
        assert seconds_diff(dt1, t2) == -2.0
        assert seconds_diff(t1, dt2) == -2.0
        assert seconds_diff(t1, t2) == -2.0

        # Swap
        dt1, dt2 = dt2, dt1
        t1, t2 = t2, t1

        assert seconds_diff(dt1, dt2) == 2.0
        assert seconds_diff(dt1, t2) == 2.0
        assert seconds_diff(t1, dt2) == 2.0
        assert seconds_diff(t1, t2) == 2.0

    def test__seconds_diff__12_hour_difference(self):
        dt1 = datetime.strptime("2022-10-04 23:59:59", "%Y-%m-%d %H:%M:%S")
        dt2_equal = datetime.strptime("2022-10-04 11:59:59", "%Y-%m-%d %H:%M:%S")
        dt2_under = datetime.strptime("2022-10-04 11:59:58", "%Y-%m-%d %H:%M:%S")
        dt2_over = datetime.strptime("2022-10-04 12:00:00", "%Y-%m-%d %H:%M:%S")

        t1 = time(23, 59, 59)
        t2_equal = time(11, 59, 59)
        t2_under = time(11, 59, 58)
        t2_over = time(12, 0, 0)

        diff_12_hours = timedelta(hours=12).total_seconds()

        # Equal
        assert (
            seconds_diff(dt1, dt2_equal)
            == diff_12_hours
            == -1 * seconds_diff(dt2_equal, dt1)
        )
        assert (
            seconds_diff(dt1, t2_equal)
            == diff_12_hours
            == -1 * seconds_diff(t2_equal, dt1)
        )
        assert (
            seconds_diff(t1, dt2_equal)
            == diff_12_hours
            == -1 * seconds_diff(dt2_equal, t1)
        )
        assert (
            seconds_diff(t1, t2_equal)
            == diff_12_hours
            == -1 * seconds_diff(t2_equal, t1)
        )

        # Under
        assert (
            seconds_diff(dt1, dt2_under)
            == diff_12_hours + 1
            == -1 * seconds_diff(dt2_under, dt1)
        )
        assert (
            seconds_diff(dt1, t2_under)
            == -1 * (diff_12_hours - 1)
            == -1 * seconds_diff(t2_under, dt1)
        )
        assert (
            seconds_diff(t1, dt2_under)
            == -1 * (diff_12_hours - 1)
            == -1 * seconds_diff(dt2_under, t1)
        )
        assert (
            seconds_diff(t1, t2_under)
            == -1 * (diff_12_hours - 1)
            == -1 * seconds_diff(t2_under, t1)
        )

        # Over
        assert (
            seconds_diff(dt1, dt2_over)
            == diff_12_hours - 1
            == -1 * seconds_diff(dt2_over, dt1)
        )
        assert (
            seconds_diff(dt1, t2_over)
            == diff_12_hours - 1
            == -1 * seconds_diff(t2_over, dt1)
        )
        assert (
            seconds_diff(t1, dt2_over)
            == diff_12_hours - 1
            == -1 * seconds_diff(dt2_over, t1)
        )
        assert (
            seconds_diff(t1, t2_over)
            == diff_12_hours - 1
            == -1 * seconds_diff(t2_over, t1)
        )

    def test__schedule_adherence__schedule_statuse_across_midnight(self):
        stop_times = parse_obj_as(
            List[StaticGtfsStopTime],
            [
                {
                    "trip_id": "trip_123",
                    "stop_id": "abc",
                    "departure_time": "23:57:02",
                    "arrival_time": "23:58:02",
                    "stop_sequence": 2,
                    "stop": {
                        "stop_id": "abc",
                        "stop_lat": 43.200001,
                        "stop_lon": 123.1000002,
                    },
                }
            ],
        )
        schedule = Schedule(stop_times=stop_times)

        vehicle_position = VehiclePosition(
            vehicle_id="veh-123",
            stop_id="abc",
            current_status=1,
            latitude=43.2,
            longitude=123.1,
            trip_id="trip_123",
            timestamp="2022-09-01 00:01:01",
        )

        schedule_status = ScheduleStatus.from_schedule(schedule, vehicle_position)

        assert schedule_status is not None
        assert schedule_status.delay == 179.0
        assert schedule_status.exact

    def test__schedule_adherence__schedule_status_basic(self):
        ScheduleStatus._current_timestamp = datetime.now()

        stop_times = parse_obj_as(
            List[StaticGtfsStopTime],
            [
                {
                    "trip_id": "trip_123",
                    "stop_id": "abc",
                    "departure_time": "12:02:02",
                    "arrival_time": "12:01:02",
                    "stop_sequence": 2,
                    "stop": {
                        "stop_id": "abc",
                        "stop_lat": 43.200001,
                        "stop_lon": 123.1000002,
                    },
                }
            ],
        )
        schedule = Schedule(stop_times=stop_times)

        vehicle_position = VehiclePosition(
            vehicle_id="veh-123",
            stop_id="abc",
            current_status=1,
            latitude=43.2,
            longitude=123.1,
            trip_id="trip_123",
            timestamp="2022-09-01 11:58:03",
        )

        schedule_status = ScheduleStatus.from_schedule(schedule, vehicle_position)

        assert schedule_status is not None
        assert schedule_status.delay == -179.0
        assert schedule_status.exact

        # With no stop ID
        vehicle_position = VehiclePosition(
            vehicle_id="veh-123",
            current_status=1,
            latitude=43.2,
            longitude=123.1,
            trip_id="trip_123",
            timestamp="2022-09-01 11:58:03",
        )

        schedule_status = ScheduleStatus.from_schedule(schedule, vehicle_position)

        assert schedule_status is not None
        assert schedule_status.delay == -179.0
        assert schedule_status.exact

        # With context
        vehicle_position = VehiclePosition(
            vehicle_id="veh-123",
            current_status=1,
            latitude=43.2,
            longitude=123.1,
            trip_id="trip_123",
            timestamp="2022-09-01 11:58:03",
        )
        stop_events = StopEvent(stop_id="veh-123", timestamp="2022-09-01 11:58:02")

        schedule_status = ScheduleStatus.from_schedule_status(
            schedule,
            vehicle_position,
            ScheduleStatus(
                trip_id="trip_123",
                vehicle_id="veh-123",
                delay=123,
                stop_events=[stop_events],
            ),
        )

        assert schedule_status is not None
        assert schedule_status.delay == -179.0
        assert schedule_status.exact

    def test__schedule__empty_stop_times(self):
        with pytest.raises(ValueError):
            Schedule(stop_times=[])

    def test__schedule_status__complete(self):
        vehicle_position = VehiclePosition(
            vehicle_id="vehicle-a",
            trip_id="10536292",
            latitude=37.76871,
            longitude=-122.389377,
            stop_id=None,
            timestamp="2022-09-01 09:19:34.042",
            current_status=None,
        )

        last_schedule_status = ScheduleStatus(
            vehicle_id="",
            trip_id="",
            delay=-1.19,
            last_updated="2022-09-01 09:19:34",
            exact=True,
            next_stop=None,
            stop_events=[
                StopEvent(stop_id="7766", timestamp="2022-09-01 09:19:29.081")
            ],
        )

        schedule = Schedule(
            stop_times=[
                StaticGtfsStopTime(
                    trip_id="10536292",
                    stop_id="7766",
                    stop_sequence=2,
                    arrival_time="09:19:34",
                    departure_time="09:19:34",
                    stop_headsign=None,
                    pickup_type=None,
                    drop_off_type=None,
                    continuous_pickup=None,
                    continuous_drop_off=None,
                    shape_dist_traveled=None,
                    timepoint=1,
                    stop=StaticGtfsStop(
                        stop_id="7766",
                        stop_name=None,
                        stop_lat=37.770513,
                        stop_lon=-122.391037,
                    ),
                ),
                StaticGtfsStopTime(
                    trip_id="10536292",
                    stop_id="7324",
                    stop_sequence=3,
                    arrival_time="09:20:40",
                    departure_time="09:20:40",
                    stop_headsign=None,
                    pickup_type=None,
                    drop_off_type=None,
                    continuous_pickup=None,
                    continuous_drop_off=None,
                    shape_dist_traveled=None,
                    timepoint=1,
                    stop=StaticGtfsStop(
                        stop_id="7324",
                        stop_name=None,
                        stop_lat=37.76871,
                        stop_lon=-122.389377,
                    ),
                ),
                StaticGtfsStopTime(
                    trip_id="10536292",
                    stop_id="7767",
                    stop_sequence=4,
                    arrival_time="09:21:59",
                    departure_time="09:21:59",
                    stop_headsign=None,
                    pickup_type=None,
                    drop_off_type=None,
                    continuous_pickup=None,
                    continuous_drop_off=None,
                    shape_dist_traveled=None,
                    timepoint=1,
                    stop=StaticGtfsStop(
                        stop_id="7767",
                        stop_name=None,
                        stop_lat=37.766864,
                        stop_lon=-122.390891,
                    ),
                ),
                StaticGtfsStopTime(
                    trip_id="10536292",
                    stop_id="7865",
                    stop_sequence=5,
                    arrival_time="09:22:33",
                    departure_time="09:22:33",
                    stop_headsign=None,
                    pickup_type=None,
                    drop_off_type=None,
                    continuous_pickup=None,
                    continuous_drop_off=None,
                    shape_dist_traveled=None,
                    timepoint=1,
                    stop=StaticGtfsStop(
                        stop_id="7865",
                        stop_name=None,
                        stop_lat=37.766722,
                        stop_lon=-122.392805,
                    ),
                ),
                StaticGtfsStopTime(
                    trip_id="10536292",
                    stop_id="7768",
                    stop_sequence=6,
                    arrival_time="09:23:48",
                    departure_time="09:23:48",
                    stop_headsign=None,
                    pickup_type=None,
                    drop_off_type=None,
                    continuous_pickup=None,
                    continuous_drop_off=None,
                    shape_dist_traveled=None,
                    timepoint=1,
                    stop=StaticGtfsStop(
                        stop_id="7768",
                        stop_name=None,
                        stop_lat=37.766492,
                        stop_lon=-122.397011,
                    ),
                ),
                StaticGtfsStopTime(
                    trip_id="10536292",
                    stop_id="7769",
                    stop_sequence=7,
                    arrival_time="09:24:38",
                    departure_time="09:24:38",
                    stop_headsign=None,
                    pickup_type=None,
                    drop_off_type=None,
                    continuous_pickup=None,
                    continuous_drop_off=None,
                    shape_dist_traveled=None,
                    timepoint=1,
                    stop=StaticGtfsStop(
                        stop_id="7769",
                        stop_name=None,
                        stop_lat=37.766287,
                        stop_lon=-122.399842,
                    ),
                ),
            ]
        )

        schedule_status = ScheduleStatus.from_schedule_status(
            schedule, vehicle_position, last_schedule_status
        )

        assert schedule_status.delay == -65.958
        assert schedule_status.stop_events[-1].stop_id == "7324"

        schedule_status = ScheduleStatus.from_schedule_status(
            schedule,
            VehiclePosition(
                vehicle_id="vehicle-a",
                trip_id="10536292",
                latitude=37.766864,
                longitude=-122.390891,
                stop_id=None,
                timestamp="2022-09-01 09:21:59.000",
                current_status=None,
            ),
            schedule_status,
        )

        # Matches stop better
        assert schedule_status.latest_stop_event.stop_id == "7767"

        schedule_status = ScheduleStatus.from_schedule_status(
            schedule,
            VehiclePosition(
                vehicle_id="vehicle-a",
                trip_id="10536292",
                latitude=37.766869,
                longitude=-122.390892,
                stop_id=None,
                timestamp="2022-09-01 09:22:05.000",
                current_status=None,
            ),
            schedule_status,
        )

        # Continue matching
        assert schedule_status.latest_stop_event.stop_id == "7865"

        schedule_status = ScheduleStatus.from_schedule_status(
            schedule,
            VehiclePosition(
                vehicle_id="vehicle-a",
                trip_id="10536292",
                latitude=37.766492,
                longitude=-122.397011,
                stop_id=None,
                timestamp="2022-09-01 09:22:06.000",
                current_status=None,
            ),
            schedule_status,
        )

        # Same stop
        assert schedule_status.latest_stop_event.stop_id == "7768"

    def test__vehicle_position_parsing(self):
        vehicle_msg = {
            b"entity_id": b"vehicle_0008",
            b"timestamp": b"1667902556",
            b"current_stop_sequence": b"0",
            b"stop_id": b"",
            b"current_status": b"2",
            b"congestion_level": b"0",
            b"occupancy_status": b"0",
            b"vehicle_id": b"8",
            b"vehicle_label": b"8",
            b"license_plate": b"",
            b"latitude": b"37.12300109863281",
            b"longitude": b"-101.45600128173828",
            b"bearing": b"90.0",
            b"odometer": b"0.0",
            b"speed": b"1.2000000476837158",
            b"trip_id": b"",
            b"route_id": b"",
            b"trip_direction_id": b"0",
            b"trip_start_time": b"",
            b"trip_start_date": b"",
            b"schedule_relationship": b"0",
        }

        VehiclePosition(**{k.decode(): v.decode() for k, v in vehicle_msg.items()})
