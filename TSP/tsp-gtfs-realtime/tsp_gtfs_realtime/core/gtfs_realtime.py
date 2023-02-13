import logging
import os
import time
from typing import Dict

import pause
import requests
from google.transit import gtfs_realtime_pb2
from gtt.service.feature_persistence import FeaturePersistenceAPI
from pydantic import FilePath, validate_arguments

from gtt.data_model.feature_persistence import FeatureNameEnum, GTFSRealtimeFeature

__all__ = ["GTFSRealtimeConfig", "GTFSRealtimeAPIPoller"]


class GTFSRealtimeConfig(GTFSRealtimeFeature):
    """Configuration data for a GTFS Realtime API Poller

    Args:
        vehicle_positions_url (HttpUrl):
            endpoint URL for VehiclePositions feed. Defaults to None
        trip_updates_url (HttpUrl):
            endpoint URL for TripUpdates feed. Defaults to None
        alerts_url (HttpUrl):
            endpoint URL for Alerts feed. Defaults to None
        vehicle_id_field (Literal["id", "label"]):
            which VehicleDescriptor field to identify a vehicle. Defaults to "id"
        max_polling_rate (PositiveFloat):
            minimum time between subsequent feed polls. Defaults to 15 seconds
        use_agency_max_rate (bool):
            whether to apply the max rate to all feeds. Default is per-feed rate
        subscribed_till (date):
            unused for now.

    Raises:
        ValueError: At least one API endpoint is required
    """

    use_agency_max_rate = False

    @classmethod
    @validate_arguments
    def from_inputs(
        cls,
        agency_id: str = None,
        should_query_feature_api: bool = True,
        config_file: FilePath = None,
    ):
        """generate Config object based on inputs from command line/env

        In order of precedence (based on args), it
          - queries the feature persistence api if `should_query_feature_api`
          - loads from the specified json file, `config_file`
          - loads from the default json file, "gtfs-realtime-api-poller.json"

        While all args are optional, a warning is logged if `config_file` is specified
        but not used because `should_query_feature_api` is set

        Args:
            feature_api_url (HttpUrl):
                base API endpoint. Defaults to None
            agency_id (str):
                agency_id matching the AgencyGUID. Defaults to None
            should_query_feature_api (bool):
                whether to query feature persistence api. Defaults to True
            config_file (FilePath):
                path to json config file to load. Defaults to "../config/gtfs-realtime-api-poller.json"

        Raises:
            ValueError: feature_api_url and agency_id are required if `should_query_feature_api`

        Returns:
            GTFSRealtimeConfig: instantiated class object
        """
        # default config file location
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        default_config_file = os.path.join(config_dir, "gtfs-realtime-api-poller.json")

        # query feature persistence api
        if should_query_feature_api:
            if config_file:
                logging.warning(
                    f"config_file provided, but {should_query_feature_api=}, disregarding config_file"
                )
            if not agency_id:
                raise ValueError(
                    "feature_api_url and agency_id are required to query feature api"
                )

            feature_api = FeaturePersistenceAPI()
            return cls.parse_obj(
                feature_api.get_feature(agency_id, FeatureNameEnum.gtfs_realtime).dict()
            )

        # else create from config_file
        logging.info(
            "initializing config from "
            + (f"{config_file=}" if config_file else f"{default_config_file=}")
        )
        return cls.parse_file(config_file or default_config_file)


class GTFSRealtimeFeed:
    """A class to handle a single feed

    When using poll() and poll_period is defined, each subsequent poll() call waits
    until poll_period seconds have elapsed before polling the feed url. This assumes
    poll_period should be enforced at the feed level. If it should be enforced at the
    agency level (therefore, less frequent polling) then poll() can explicitly be given
    the POSIX time to pause until. If neither provided, it polls without waiting

    Args:
        url: GTFS Realtime feed URL
        poll_period (optional): time to enforce between poll() calls
    """

    def __init__(self, url, poll_period=None, headers: Dict[str, str] = None):
        self.url = url
        self.feed = gtfs_realtime_pb2.FeedMessage()
        self.poll_period = poll_period
        self.headers = headers
        self._next_poll_time = time.time()

    def poll(self, wait_until=None):
        if wait_until or self.poll_period:
            pause.until(wait_until or self._next_poll_time)
            self._next_poll_time = time.time() + self.poll_period
        response = requests.get(self.url, headers=self.headers)
        if response.status_code > 299:
            logging.error(
                f"Error retrieving feed (status {response.status_code}): {response.content}"
            )
        self.feed.ParseFromString(response.content)


class GTFSRealtimeAPIPoller:
    """A class to poll an agency's gtfs-realtime api endpoint

    Args:
        config (str or gtfs_realtime_poller_api.Config): filename or Config object
    """

    def __init__(self, config: GTFSRealtimeConfig = None, **kwargs):
        _cfg = config or GTFSRealtimeConfig(**kwargs)

        self.use_agency_max_rate = _cfg.use_agency_max_rate
        self.max_polling_rate = _cfg.max_polling_rate
        feed_max = self.max_polling_rate if not self.use_agency_max_rate else None
        self._next_poll_time = time.time()

        self.vehicle_id_field = _cfg.vehicle_id_field

        self._vehicle_positions = GTFSRealtimeFeed(
            url=_cfg.vehicle_positions_url,
            poll_period=feed_max,
            headers=_cfg.vehicle_positions_headers,
        )
        self._trip_updates = GTFSRealtimeFeed(
            url=_cfg.trip_updates_url,
            poll_period=feed_max,
            headers=_cfg.trip_updates_headers,
        )
        self._alerts = GTFSRealtimeFeed(
            url=_cfg.alerts_url, poll_period=feed_max, headers=_cfg.alerts_headers
        )

    def poll_vehicle_positions(self):
        self._vehicle_positions.poll(wait_until=self.next_poll_time)
        self.update_next_poll_time()

    def poll_trip_updates(self):
        self._trip_updates.poll(wait_until=self.next_poll_time)
        self.update_next_poll_time()

    def poll_alerts(self):
        self._alerts.poll(wait_until=self.next_poll_time)
        self.update_next_poll_time()

    def update_next_poll_time(self):
        if self.use_agency_max_rate:
            self._next_poll_time = time.time() + self.max_polling_rate

    @property
    def next_poll_time(self):
        """the POSIX timestamp when the next poll can occur if enforcing
        max_polling_rate across all agency feeds. If enforcing per-feed, returns None

        Returns:
            int or NoneType: POSIX time in seconds
        """
        return self._next_poll_time if self.use_agency_max_rate else None

    @property
    def last_updated(self):
        """the timestamp of the most recently updated feed

        Returns:
            int: POSIX time in seconds
        """
        return max(
            self._vehicle_positions.feed.header.timestamp,
            self._trip_updates.feed.header.timestamp,
            self._alerts.feed.header.timestamp,
        )

    @property
    def vehicle_positions_last_updated(self):
        """the timestamp of the most recent vehicle_positions feed

        Returns:
            int: POSIX time in seconds
        """
        return self._vehicle_positions.feed.header.timestamp

    @property
    def trip_updates_last_updated(self):
        """the timestamp of the most recent trip_updates feed

        Returns:
            int: POSIX time in seconds
        """
        return self._trip_updates.feed.header.timestamp

    @property
    def alerts_last_updated(self):
        """the timestamp of the most recent alerts feed

        Returns:
            int: POSIX time in seconds
        """
        return self._alerts.feed.header.timestamp

    @property
    def vehicle_positions(self):
        """returns a list of (key, field) for updating redis database using
        vehicle position id and the following list of optional attributes:
          - timestamp
          - current_stop_sequence
          - stop_id
          - current_status: (INCOMING_AT, STOPPED_AT, IN_TRANSIT_TO)
          - congestion_level: (UNKNOWN_CONGESTION_LEVEL, RUNNING_SMOOTHLY, STOP_AND_GO, CONGESTION, SEVERE_CONGESTION)
          - occupancy_status: (EMPTY, MANY_SEATS_AVAILABLE, FEW_SEATS_AVAILABLE, STANDING_ROOM_ONLY, CRUSHED_STANDING_ROOM_ONLY, FULL, NOT_ACCEPTING_PASSENGERS)
          (VehicleDescriptor)
          - vehicle_id
          - vehicle_label
          - license_plate
          (Position)
          - latitude
          - longitude
          - bearing
          - odometer
          - speed
          (TripDescriptor)
          - trip_id
          - route_id
          - trip_direction_id
          - trip_start_time
          - trip_start_date
          - schedule_relationship: (SCHEDULED, ADDED, UNSCHEDULED, CANCELED)

        more information on specific fields can be found here:
        https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto#:~:text=message%20VehiclePosition

        Note: currently, all fields are updated even though many are not used.
        Alternatively, a list of available fields can be implemented to only return
        fields that are provided by the API. space/complexity tradeoff

        It might be better to use the actual nesting rather than manually flattening.
        This likely depends on the needs for more complicated querying and indexing
        capabilities needed by a subscriber.
          ("trip_id": vehicle_position.vehicle.trip.trip_id)


        Returns:
            [(str, dict)]: vehicle id and attributes
        """
        return [
            (
                getattr(entity.vehicle.vehicle, self.vehicle_id_field),
                {
                    "entity_id": entity.id,
                    "timestamp": entity.vehicle.timestamp,
                    "current_stop_sequence": entity.vehicle.current_stop_sequence,
                    "stop_id": entity.vehicle.stop_id,
                    "current_status": entity.vehicle.current_status,
                    "congestion_level": entity.vehicle.congestion_level,
                    "occupancy_status": entity.vehicle.occupancy_status,
                    # VehicleDescriptor
                    "vehicle_id": entity.vehicle.vehicle.id,
                    "vehicle_label": entity.vehicle.vehicle.label,
                    "license_plate": entity.vehicle.vehicle.license_plate,
                    # Position
                    "latitude": entity.vehicle.position.latitude,
                    "longitude": entity.vehicle.position.longitude,
                    "bearing": entity.vehicle.position.bearing,
                    "odometer": entity.vehicle.position.odometer,
                    "speed": entity.vehicle.position.speed,
                    # TripDescriptor
                    "trip_id": entity.vehicle.trip.trip_id,
                    "route_id": entity.vehicle.trip.route_id,
                    "trip_direction_id": entity.vehicle.trip.direction_id,
                    "trip_start_time": entity.vehicle.trip.start_time,
                    "trip_start_date": entity.vehicle.trip.start_date,
                    "schedule_relationship": entity.vehicle.trip.schedule_relationship,
                },
            )
            for entity in self._vehicle_positions.feed.entity
            if entity.HasField("vehicle")
        ]

    @property
    def vehicle_positions_sparse(self):
        """returns a list of (key, field) similar to vehicle_positions, but does not
        populate values that are not provided.

        This is potentially useful if needing to differentiate between 0 and None, but
        this can almost certainly be improved by using entity.ListFields(), just
        explicitly setting values to None, or even providing a generator instead of the
        entire list of entities at once to save memory.
        """
        return [
            (
                getattr(entity.vehicle.vehicle, self.vehicle_id_field),
                {
                    k: v
                    for k, v, has_field in [
                        (
                            "entity_id",
                            entity.id,
                            True,
                        ),
                        (
                            "timestamp",
                            entity.vehicle.timestamp,
                            entity.vehicle.HasField("timestamp"),
                        ),
                        (
                            "current_stop_sequence",
                            entity.vehicle.current_stop_sequence,
                            entity.vehicle.HasField("current_stop_sequence"),
                        ),
                        (
                            "stop_id",
                            entity.vehicle.stop_id,
                            entity.vehicle.HasField("stop_id"),
                        ),
                        (
                            "current_status",
                            entity.vehicle.current_status,
                            entity.vehicle.HasField("current_status"),
                        ),
                        (
                            "congestion_level",
                            entity.vehicle.congestion_level,
                            entity.vehicle.HasField("congestion_level"),
                        ),
                        (
                            "occupancy_status",
                            entity.vehicle.occupancy_status,
                            entity.vehicle.HasField("occupancy_status"),
                        ),
                        # VehicleDescriptor
                        (
                            "vehicle_id",
                            entity.vehicle.vehicle.id,
                            entity.vehicle.vehicle.HasField("id"),
                        ),
                        (
                            "vehicle_label",
                            entity.vehicle.vehicle.label,
                            entity.vehicle.vehicle.HasField("label"),
                        ),
                        (
                            "license_plate",
                            entity.vehicle.vehicle.license_plate,
                            entity.vehicle.vehicle.HasField("license_plate"),
                        ),
                        # Position
                        (
                            "latitude",
                            entity.vehicle.position.latitude,
                            entity.vehicle.position.HasField("latitude"),
                        ),
                        (
                            "longitude",
                            entity.vehicle.position.longitude,
                            entity.vehicle.position.HasField("longitude"),
                        ),
                        (
                            "bearing",
                            entity.vehicle.position.bearing,
                            entity.vehicle.position.HasField("bearing"),
                        ),
                        (
                            "odometer",
                            entity.vehicle.position.odometer,
                            entity.vehicle.position.HasField("odometer"),
                        ),
                        (
                            "speed",
                            entity.vehicle.position.speed,
                            entity.vehicle.position.HasField("speed"),
                        ),
                        # TripDescriptor
                        (
                            "trip_id",
                            entity.vehicle.trip.trip_id,
                            entity.vehicle.trip.HasField("trip_id"),
                        ),
                        (
                            "route_id",
                            entity.vehicle.trip.route_id,
                            entity.vehicle.trip.HasField("route_id"),
                        ),
                        (
                            "trip_direction_id",
                            entity.vehicle.trip.direction_id,
                            entity.vehicle.trip.HasField("direction_id"),
                        ),
                        (
                            "trip_start_time",
                            entity.vehicle.trip.start_time,
                            entity.vehicle.trip.HasField("start_time"),
                        ),
                        (
                            "trip_start_date",
                            entity.vehicle.trip.start_date,
                            entity.vehicle.trip.HasField("start_date"),
                        ),
                        (
                            "schedule_relationship",
                            entity.vehicle.trip.schedule_relationship,
                            entity.vehicle.trip.HasField("schedule_relationship"),
                        ),
                    ]
                    if has_field
                },
            )
            for entity in self._vehicle_positions.feed.entity
            if entity.HasField("vehicle")
        ]

    @property
    def trip_updates(self):
        """returns a list of (key, field) for updating redis database using
        trip update id and the following list of optional attributes:
          - timestamp
          - delay
          (TripDescriptor)
          - trip_id
          - route_id
          - trip_direction_id
          - trip_start_time
          - trip_start_date
          - schedule_relationship: (SCHEDULED, ADDED, UNSCHEDULED, CANCELED)
          (VehicleDescriptor)
          - vehicle_id
          - vehicle_label
          - license_plate
          (StopTimeUpdate) - repeated
          - stop_time_updates
            - stop_sequence
            - stop_id
            (StopTimeEvent)
            - arrival_delay
            - arrival_time
            - arrival_uncertainty
            (StopTimeEvent)
            - departure_delay
            - departure_time
            - departure_uncertainty

        more information on specific fields can be found here:
        https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto#:~:text=message%20TripUpdate


        Returns:
            [(str, dict)]: trip id and attributes
        """
        return [
            (
                entity.trip_update.trip.trip_id,
                {
                    "timestamp": entity.trip_update.timestamp,
                    "delay": entity.trip_update.delay,
                    # TripDescriptor
                    "trip_id": entity.trip_update.trip.trip_id,
                    "route_id": entity.trip_update.trip.route_id,
                    "trip_direction_id": entity.trip_update.trip.direction_id,
                    "trip_start_time": entity.trip_update.trip.start_time,
                    "trip_start_date": entity.trip_update.trip.start_date,
                    "schedule_relationship": entity.trip_update.trip.schedule_relationship,
                    # VehicleDescriptor
                    "vehicle_id": entity.trip_update.vehicle.id,
                    "vehicle_label": entity.trip_update.vehicle.label,
                    "license_plate": entity.trip_update.vehicle.license_plate,
                    # StopTimeUpdate - repeated
                    "stop_time_updates": [
                        {
                            "stop_sequence": stop_time_update.stop_sequence,
                            "stop_id": stop_time_update.stop_id,
                            # StopTimeEvent
                            "arrival_delay": stop_time_update.arrival.delay,
                            "arrival_time": stop_time_update.arrival.time,
                            "arrival_uncertainty": stop_time_update.arrival.uncertainty,
                            # StopTimeEvent
                            "departure_delay": stop_time_update.departure.delay,
                            "departure_time": stop_time_update.departure.time,
                            "departure_uncertainty": stop_time_update.departure.uncertainty,
                        }
                        for stop_time_update in entity.trip_update.stop_time_update
                    ],
                },
            )
            for entity in self._trip_updates.feed.entity
            if entity.HasField("trip_update")
        ]

    @property
    def trip_updates_sparse(self):
        """returns a list of (key, field) similar to trip_updates, but does not
        populate values that are not provided.

        This is potentially useful if needing to differentiate between 0 and None, but
        this can almost certainly be improved by using entity.ListFields(), just
        explicitly setting values to None, or even providing a generator instead of the
        entire list of entities at once to save memory.
        """
        return [
            (
                entity.trip_update.trip.trip_id,
                {
                    k: v
                    for k, v, has_field in [
                        (
                            "entity_id",
                            entity.id,
                            True,
                        ),
                        (
                            "timestamp",
                            entity.trip_update.timestamp,
                            entity.trip_update.HasField("timestamp"),
                        ),
                        (
                            "delay",
                            entity.trip_update.delay,
                            entity.trip_update.HasField("delay"),
                        ),
                        # TripDescriptor
                        (
                            "trip_id",
                            entity.trip_update.trip.trip_id,
                            entity.trip_update.trip.HasField("trip_id"),
                        ),
                        (
                            "route_id",
                            entity.trip_update.trip.route_id,
                            entity.trip_update.trip.HasField("route_id"),
                        ),
                        (
                            "trip_direction_id",
                            entity.trip_update.trip.direction_id,
                            entity.trip_update.trip.HasField("direction_id"),
                        ),
                        (
                            "trip_start_time",
                            entity.trip_update.trip.start_time,
                            entity.trip_update.trip.HasField("start_time"),
                        ),
                        (
                            "trip_start_date",
                            entity.trip_update.trip.start_date,
                            entity.trip_update.trip.HasField("start_date"),
                        ),
                        (
                            "schedule_relationship",
                            entity.trip_update.trip.schedule_relationship,
                            entity.trip_update.trip.HasField("schedule_relationship"),
                        ),
                        # VehicleDescriptor
                        (
                            "vehicle_id",
                            entity.trip_update.vehicle.id,
                            entity.trip_update.vehicle.HasField("id"),
                        ),
                        (
                            "vehicle_label",
                            entity.trip_update.vehicle.label,
                            entity.trip_update.vehicle.HasField("label"),
                        ),
                        (
                            "license_plate",
                            entity.trip_update.vehicle.license_plate,
                            entity.trip_update.vehicle.HasField("license_plate"),
                        ),
                        # StopTimeUpdate - repeated
                        (
                            "stop_time_updates",
                            [
                                {
                                    stu_k: stu_v
                                    for stu_k, stu_v, stu_has_field in [
                                        (
                                            "stop_sequence",
                                            stu.stop_sequence,
                                            stu.HasField("stop_sequence"),
                                        ),
                                        (
                                            "stop_id",
                                            stu.stop_id,
                                            stu.HasField("stop_id"),
                                        ),
                                        # StopTimeEvent
                                        (
                                            "arrival_delay",
                                            stu.arrival.delay,
                                            stu.arrival.HasField("delay"),
                                        ),
                                        (
                                            "arrival_time",
                                            stu.arrival.time,
                                            stu.arrival.HasField("time"),
                                        ),
                                        (
                                            "arrival_uncertainty",
                                            stu.arrival.uncertainty,
                                            stu.arrival.HasField("uncertainty"),
                                        ),
                                        # StopTimeEvent
                                        (
                                            "departure_delay",
                                            stu.departure.delay,
                                            stu.departure.HasField("delay"),
                                        ),
                                        (
                                            "departure_time",
                                            stu.departure.time,
                                            stu.departure.HasField("time"),
                                        ),
                                        (
                                            "departure_uncertainty",
                                            stu.departure.uncertainty,
                                            stu.departure.HasField("uncertainty"),
                                        ),
                                    ]
                                    if stu_has_field
                                }
                                for stu in entity.trip_update.stop_time_update
                            ],
                            True,
                        ),
                    ]
                    if has_field
                },
            )
            for entity in self._trip_updates.feed.entity
            if entity.HasField("trip_update")
        ]

    @property
    def alerts(self):
        """returns a list of (key, field) for updating redis database using
        alert id and the following list of optional attributes:
          - header_text
          - description_text
          - additional_information_url
          - cause: (UNKNOWN_CAUSE, OTHER_CAUSE, TECHNICAL_PROBLEM, STRIKE, DEMONSTRATION, ACCIDENT, HOLIDAY, WEATHER, MAINTENANCE, CONSTRUCTION, POLICE_ACTIVITY, MEDICAL_EMERGENCY)
          - effect: (NO_SERVICE, REDUCED_SERVICE, SIGNIFICANT_DELAYS, DETOUR, ADDITIONAL_SERVICE, MODIFIED_SERVICE, OTHER_EFFECT, UNKNOWN_EFFECT, STOP_MOVED)
          (TimeRange) - repeated
          - active_periods
            - start
            - end
          (EntitySelector) - repeated
          - informed_entities
            - agency_id
            - route_id
            - route_type
            - stop_id
            (TripDescriptor)
            - trip_id
            - trip_route_id
            - trip_direction_id
            - trip_start_time
            - trip_start_date
            - trip_schedule_relationship: (SCHEDULED, ADDED, UNSCHEDULED, CANCELED)

        more information on specific fields can be found here:
        https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto#:~:text=message%20Alert


        Returns:
            [(str, dict)]: vehicle id and attributes
        """
        return [
            (
                entity.id,
                {
                    "header_text": entity.alert.header_text,
                    "description_text": entity.alert.description_text,
                    "additional_information_url": entity.alert.url,
                    "cause": entity.alert.cause,
                    "effect": entity.alert.effect,
                    # TimeRange - repeated
                    "active_periods": [
                        {
                            "start": active_period.start,
                            "end": active_period.end,
                        }
                        for active_period in entity.alert.active_period
                    ],
                    # EntitySelector - repeated
                    "informed_entities": [
                        {
                            "agency_id": informed_entity.agency_id,
                            "route_id": informed_entity.route_id,
                            "route_type": informed_entity.route_type,
                            "stop_id": informed_entity.stop_id,
                            "trip_id": informed_entity.trip.trip_id,
                            "trip_route_id": informed_entity.trip.route_id,
                            "trip_direction_id": informed_entity.trip.direction_id,
                            "trip_start_time": informed_entity.trip.start_time,
                            "trip_start_date": informed_entity.trip.start_date,
                            "trip_schedule_relationship": informed_entity.trip.schedule_relationship,
                        }
                        for informed_entity in entity.alert.informed_entity
                    ],
                },
            )
            for entity in self._alerts.feed.entity
            if entity.HasField("alert")
        ]

    @property
    def alerts_sparse(self):
        """returns a list of (key, field) similar to alerts, but does not
        populate values that are not provided.

        This is potentially useful if needing to differentiate between 0 and None, but
        this can almost certainly be improved by using entity.ListFields(), just
        explicitly setting values to None, or even providing a generator instead of the
        entire list of entities at once to save memory.
        """
        return [
            (
                entity.id,
                {
                    k: v
                    for k, v, has_field in [
                        (
                            "header_text",
                            entity.alert.header_text,
                            entity.alert.HasField("header_text"),
                        ),
                        (
                            "description_text",
                            entity.alert.description_text,
                            entity.alert.HasField("description_text"),
                        ),
                        (
                            "additional_information_url",
                            entity.alert.url,
                            entity.alert.HasField("url"),
                        ),
                        (
                            "cause",
                            entity.alert.cause,
                            entity.alert.HasField("cause"),
                        ),
                        (
                            "effect",
                            entity.alert.effect,
                            entity.alert.HasField("effect"),
                        ),
                        # TimeRange - repeated
                        (
                            "active_periods",
                            [
                                {
                                    ap_k: ap_v
                                    for ap_k, ap_v, ap_has_field in [
                                        (
                                            "start",
                                            active_period.start,
                                            active_period.HasField("start"),
                                        ),
                                        (
                                            "end",
                                            active_period.end,
                                            active_period.HasField("end"),
                                        ),
                                    ]
                                    if ap_has_field
                                }
                                for active_period in entity.alert.active_period
                            ],
                            True,
                        ),
                        # EntitySelector - repeated
                        (
                            "informed_entities",
                            [
                                {
                                    ie_k: ie_v
                                    for ie_k, ie_v, ie_has_field in [
                                        (
                                            "agency_id",
                                            ie.agency_id,
                                            ie.HasField("agency_id"),
                                        ),
                                        (
                                            "route_id",
                                            ie.route_id,
                                            ie.HasField("route_id"),
                                        ),
                                        (
                                            "route_type",
                                            ie.route_type,
                                            ie.HasField("route_type"),
                                        ),
                                        (
                                            "stop_id",
                                            ie.stop_id,
                                            ie.HasField("stop_id"),
                                        ),
                                        (
                                            "trip_id",
                                            ie.trip.trip_id,
                                            ie.trip.HasField("trip_id"),
                                        ),
                                        (
                                            "trip_route_id",
                                            ie.trip.route_id,
                                            ie.trip.HasField("route_id"),
                                        ),
                                        (
                                            "trip_direction_id",
                                            ie.trip.direction_id,
                                            ie.trip.HasField("direction_id"),
                                        ),
                                        (
                                            "trip_start_time",
                                            ie.trip.start_time,
                                            ie.trip.HasField("start_time"),
                                        ),
                                        (
                                            "trip_start_date",
                                            ie.trip.start_date,
                                            ie.trip.HasField("start_date"),
                                        ),
                                        (
                                            "trip_schedule_relationship",
                                            ie.trip.schedule_relationship,
                                            ie.trip.HasField("schedule_relationship"),
                                        ),
                                    ]
                                    if ie_has_field
                                }
                                for ie in entity.alert.informed_entity
                            ],
                            True,
                        ),
                    ]
                    if has_field
                },
            )
            for entity in self._alerts.feed.entity
            if entity.HasField("alert")
        ]
