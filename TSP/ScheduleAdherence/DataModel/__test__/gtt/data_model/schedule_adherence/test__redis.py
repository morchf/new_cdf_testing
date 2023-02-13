import pytest

from gtt.data_model.schedule_adherence import RedisChannel


class ScheduleAdherenceChannel(RedisChannel):
    channel_namespace = "tsp_in_cloud"
    channel_format = "trip_delay:{agency_id}:{trip_id}:{vehicle_id}"


class StaticGtfsChannel(RedisChannel):
    channel_namespace = "tsp_in_cloud"
    channel_format = "static_gtfs:{agency_id}:{trip_id}"


class TestChannel:
    def test__schedule_adherence_channel__empty(self):
        assert ScheduleAdherenceChannel.all() == "tsp_in_cloud:trip_delay:*"
        assert ScheduleAdherenceChannel.cache() == "tsp_in_cloud:trip_delay:*"
        assert ScheduleAdherenceChannel.new() == "tsp_in_cloud:new_trip_delay:*"
        assert StaticGtfsChannel.all() == "tsp_in_cloud:static_gtfs:*"

    def test__schedule_adherence_channel__filled(self):
        assert (
            ScheduleAdherenceChannel.cache(trip_id="123")
            == "tsp_in_cloud:trip_delay:*:123:*"
        )
        assert (
            ScheduleAdherenceChannel.cache(agency_id="agy", trip_id="123")
            == "tsp_in_cloud:trip_delay:agy:123:*"
        )
        assert (
            ScheduleAdherenceChannel.cache(
                agency_id="agy", trip_id="123", vehicle_id="veh2"
            )
            == "tsp_in_cloud:trip_delay:agy:123:veh2"
        )

        assert (
            ScheduleAdherenceChannel.new(
                agency_id="agy", trip_id="123", vehicle_id="veh2"
            )
            == "tsp_in_cloud:new_trip_delay:agy:123:veh2"
        )

    def test__channel__with_other_channel(self):
        assert ScheduleAdherenceChannel.default_channel_kwargs() == {
            "agency_id": "*",
            "trip_id": "*",
            "vehicle_id": "*",
        }
        assert StaticGtfsChannel.default_channel_kwargs() == {
            "agency_id": "*",
            "trip_id": "*",
        }

    def test__parse__basic(self):
        values = ScheduleAdherenceChannel.parse("tsp_in_cloud:trip_delay:agy:*:veh")

        assert values["agency_id"] == "agy"
        assert values["trip_id"] == "*"
        assert values["vehicle_id"] == "veh"

    def test__parse__glob(self):
        values = ScheduleAdherenceChannel.parse("tsp_in_cloud:trip_delay:*")

        assert values["agency_id"] == "*"
        assert values["trip_id"] == "*"
        assert values["vehicle_id"] == "*"

        values = ScheduleAdherenceChannel.parse("tsp_in_cloud:trip_delay:agy:*")

        assert values["agency_id"] == "agy"
        assert values["trip_id"] == "*"
        assert values["vehicle_id"] == "*"

        values = ScheduleAdherenceChannel.parse("tsp_in_cloud:trip_delay:agy:*:veh:*")

        assert values["agency_id"] == "agy"
        assert values["trip_id"] == "*"
        assert values["vehicle_id"] == "veh"

    def test__parse__invalid_format(self):
        with pytest.raises(ValueError):
            ScheduleAdherenceChannel.parse("xyz:abc:*")
