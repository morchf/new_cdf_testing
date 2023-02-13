from typing import Any, Dict, List, Optional

from pydantic import parse_obj_as

from gtt.data_model.schedule_adherence import (
    StaticGtfsStop,
    StaticGtfsStopTime,
    StaticGtfsTrip,
)


class StaticGtfsQueries:
    DATE_QUERY = """
        SELECT MAX(last_updated) AS last_updated
        FROM routes
        WHERE cms_id = '{agency_id}'
    """
    TRIPS_QUERY = """
        SELECT *
        FROM trips
        WHERE cms_id = '{agency_id}'
        AND trip_id = '{trip_id}'
    """
    STOP_QUERY = """
        SELECT *
        FROM stops
        WHERE cms_id = '{agency_id}'
        AND stop_id = '{stop_id}'
    """
    # Convert stop times in agency timezone to UTC
    # Must convert 'TIME' type to 'TIMEZONE' to properly handle conversion
    STOP_TIMES_QUERY = """
        WITH static_gtfs_agency AS (
            SELECT agency_timezone AS tz
            FROM agency
            WHERE cms_id = '{agency_id}'
        )
        SELECT
            st.trip_id,
            st.stop_id,
            st.stop_sequence,
            st.timepoint,
            (
                TIMEZONE(
                    (SELECT tz FROM static_gtfs_agency),
                    (CURRENT_DATE + st.arrival_time::TIME)
                ) - CURRENT_DATE
            )::TIME AS arrival_time,
            (
                TIMEZONE(
                    (SELECT tz FROM static_gtfs_agency),
                    (CURRENT_DATE + st.departure_time::TIME)
                ) - CURRENT_DATE
            )::TIME AS departure_time
        FROM stop_times st
        WHERE cms_id = '{agency_id}'
        AND trip_id = '{trip_id}'
    """
    STOP_TIMES_STOPS_QUERY = """
        WITH static_gtfs_agency AS (
            SELECT agency_timezone AS tz
            FROM agency
            WHERE cms_id = '{agency_id}'
        ),
        static_gtfs_stops AS (
            SELECT *
            FROM stops
            WHERE cms_id = '{agency_id}'
        ),
        static_gtfs_stop_times AS (
            SELECT *
            FROM stop_times st
            WHERE cms_id = '{agency_id}'
            AND trip_id = '{trip_id}'
        )
        SELECT
            st.trip_id,
            st.stop_sequence,
            st.timepoint,
            (
                TIMEZONE(
                    (SELECT tz FROM static_gtfs_agency),
                    (CURRENT_DATE + st.arrival_time::TIME)
                ) - CURRENT_DATE
            )::TIME AS arrival_time,
            (
                TIMEZONE(
                    (SELECT tz FROM static_gtfs_agency),
                    (CURRENT_DATE + st.departure_time::TIME)
                ) - CURRENT_DATE
            )::TIME AS departure_time,
            s.*
        FROM static_gtfs_stop_times st
        JOIN static_gtfs_stops s USING (stop_id)
        ORDER BY stop_sequence
    """


class StaticGtfsService:
    _sql_client: Any
    _sql_kwargs: Dict[str, str]

    def __init__(self, sql_client, *, sql_kwargs: Optional[Dict[str, Any]] = None):
        self._sql_client = sql_client
        self._sql_kwargs = {} if sql_kwargs is None else sql_kwargs

    def get_date(self, agency_id: str) -> str:
        """Latest static GTFS load date for an agency

        Args:
            agency_id (str): Agency GUID

        Returns:
            str: Date as a string (yyyy-mm-dd)
        """
        response = self._sql_client.execute(
            StaticGtfsQueries.DATE_QUERY, agency_id=agency_id, **self._sql_kwargs
        )

        if response is None or len(response) == 0:
            raise Exception("No static GTFS found for agency")

        return response[0].get("last_updated")

    def get_trip(self, agency_id: str, trip_id: str) -> StaticGtfsTrip:
        response = self._sql_client.execute(
            StaticGtfsQueries.TRIPS_QUERY,
            agency_id=agency_id,
            trip_id=trip_id,
            **self._sql_kwargs
        )

        if response is None:
            raise Exception("Trip not found")

        return next(iter(parse_obj_as(List[StaticGtfsTrip], response)), None)

    def get_stop(self, agency_id: str, stop_id: str) -> StaticGtfsStop:
        response = self._sql_client.execute(
            StaticGtfsQueries.STOP_QUERY,
            agency_id=agency_id,
            stop_id=stop_id,
            **self._sql_kwargs
        )

        if response is None:
            raise Exception("Stop not found")

        return next(iter(parse_obj_as(List[StaticGtfsStop], response)), None)

    def get_stop_times(
        self, agency_id: str, trip_id: str, complete: Optional[bool] = True
    ) -> List[StaticGtfsStopTime]:
        response = self._sql_client.execute(
            StaticGtfsQueries.STOP_TIMES_STOPS_QUERY
            if complete
            else StaticGtfsQueries.STOP_TIMES_QUERY,
            agency_id=agency_id,
            trip_id=trip_id,
            **self._sql_kwargs
        )

        if response is None:
            raise Exception("Stop not found")

        stop_times = parse_obj_as(List[StaticGtfsStopTime], response)

        if not complete:
            return stop_times

        # Match stops to stop times
        stops = parse_obj_as(List[StaticGtfsStop], response)

        if not len(stops) > 0:
            return stop_times

        stops = {stop.stop_id: stop for stop in stops}

        # Add stops to stop times
        for stop_time in stop_times:
            stop_time.stop = stops.get(stop_time.stop_id)

        return stop_times
