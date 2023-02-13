import logging
import threading
from dataclasses import dataclass
from datetime import datetime

import boto3
from redis import Redis

from gtt.data_model.rt_radio_message import GPSData
from tsp_gtfs_realtime.core.estimation import PositionEstimationBase


@dataclass
class Config:
    local_development: bool = True
    redis_url: str = "localhost"
    redis_port: int = 6379
    # ToDo: change for elasticache connection
    use_ssl: bool = False
    username: str = None
    password: str = None


class AWSRedisBase:
    def __init__(self, config=Config(), redis=None):
        # set up authentication
        if not config.local_development:
            self.credentials = boto3.Session().get_credentials()
            self.elasticache_client = boto3.client("elasticache")
        self.redis = redis or Redis(
            host=config.redis_url,
            port=config.redis_port,
            db=0,
            decode_responses=True,
            ssl=config.use_ssl,
            username=config.username,
            password=config.password,
        )
        # test connection
        self.redis.ping()


class AWSRedisSubscriber(AWSRedisBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pubsub = self.redis.pubsub()


class AWSRedisEntitySubscriber(AWSRedisBase):
    """A base class for a redis subscriber using the pubsub channel for new data alerts

    For some redis key, `key`, using this paradigm, a message is sent on a corresponding
    `channel` with "new_" prepended to the relevant part of the key.

    For example,
    key:      `agency_name`:vehicle_position:`vehicle_id`
    channel:  `agency_name`:new_vehicle_position:`vehicle_id`

    `_data` is an internal variable protected by `_data_lock` to provide a thread-safe
    accessor between the main and background thread for updating `data`

    `message_handler` runs in a background thread to handle a new message on `channel`
    and get the data at `key`. This is expected to be overridden by an inheriting
    class, but a default handler is provided that gets a string stored at `key` and
    saves it to `_data` using the `_data_lock`.

    Args:
        agency_name (str):
            used to namespace agency data within redis
        key (str):
            redis key to use when retrieving new data (without agency_name prepended)
        channel (str):
            (optional) redis pubsub channel name(without agency_name prepended)
            if not provided, it is set to f"new_{key}"
        timeout:
            (not yet implemented) time to wait between new data before raising
            a TimeoutError
    """

    def __init__(self, agency_name, key, channel=None, timeout=None, **kwargs):
        super().__init__(**kwargs)
        self.pubsub = self.redis.pubsub()

        self.agency_name = agency_name
        self.key = f"{self.agency_name}:{key}"
        channel = channel or f"new_{key}"
        self.channel = f"{self.agency_name}:{channel}"

        # ToDo: TimeoutError if no fresh data within timeout
        if timeout:
            raise NotImplementedError

        self._data = None
        self._data_lock = threading.Lock()

        # keep track of the time last updated, and whether it has been accessed yet
        self.data_last_updated = None
        self.has_fresh_data = False
        self.data_count = 0

        # subscribe to channel with handler to run in background
        logging.info(f"subscribing to {self.channel}")
        self.pubsub.subscribe(**{self.channel: self.message_handler})
        self.pubsub.check_health()
        # start subscriber thread as daemon to stop along with main thread
        self._pubsub_thread = self.pubsub.run_in_thread(sleep_time=60, daemon=True)

    @property
    def data(self):
        """Thread-safe accessor"""
        # wait for handler thread to unlock if setting new data
        with self._data_lock:
            self.has_fresh_data = False
            return self._data

    @data.setter
    def data(self, value):
        with self._data_lock:
            self._data = value
            self.has_fresh_data = True
            self.data_count += 1
            self.data_last_updated = datetime.now()

    def message_handler(self, message):
        raise NotImplementedError


class AgencyLastUpdatedSubscriber(AWSRedisEntitySubscriber):
    """Class to get the most recent `last_updated` data in a background thread

    watches for pubsub `new_agency_data` messages, then gets the `last_updated` time.

    `channel_last_updated`: the time of the last pubsub message
    `agency_last_updated`: the actual time the agency was last updated

    Args:
        agency_name (str):
            used to namespace agency data within redis
    """

    def __init__(self, agency_name, **kwargs):
        key = "last_updated"
        channel = "new_agency_data"
        super().__init__(agency_name, key, channel, **kwargs)

    @property
    def channel_last_updated(self):
        return self.data_last_updated

    @property
    def agency_last_updated(self):
        return datetime.fromtimestamp(float(self.data)) if self.data else None

    def message_handler(self, message):
        logging.debug(f"pubsub {message}")
        self.data = self.redis.get(self.key)


class VehicleSubscriber(AWSRedisEntitySubscriber):
    """Class to get the most recent `vehicle_position` data in a background thread

    watches for pubsub `new_vehicle_position` messages, then gets `vehicle_position`
    hash set to get the timestamp and gps_data

    `timestamp`: timestamp in vehicle_position
    `gps_data`:
       - latitude:  Degrees North, in the WGS-84 coordinate system
       - longitude: Degrees East, in the WGS-84 coordinate system
       - speed:     Momentary speed measured by the vehicle, in kilometers per hour
       - heading:   Degrees clockwise from North. This can be compass bearing or the
                    direction toward the next stop

    Args:
        agency_name (str):
            used to namespace agency data within redis
        vehicle_id (str):
            vehicle_id used to identify vehicle_position instance
        trip_id (str):
            trip_id used to identify which trip is expected to be initially associated
        estimator (PositionEstimationBase, optional):
            derived PositionEstimation class to predict data between updates
    """

    def __init__(
        self,
        agency_name,
        vehicle_id,
        trip_id=None,
        estimator: PositionEstimationBase = None,
        **kwargs,
    ):
        key = f"vehicle_position:{vehicle_id}"
        self._timestamp = None
        self.vehicle_id = vehicle_id
        self.trip_id = trip_id
        self._estimator = estimator
        super().__init__(agency_name, key, **kwargs)

    @property
    def timestamp(self):
        return (
            datetime.fromtimestamp(float(self._timestamp)) if self._timestamp else None
        )

    @property
    def gps_data(self):
        """Thread-safe accessor

        If estimator was provided, position is estimated based on current time

        ToDo: abstract gps_data to its own class to better handle truthiness, attribute
        checking, units, and formatted accessors instead of dealing with list/dict

        Returns:
            GPSData object: gps_data, or None if no valid data received
        """
        return self._estimator.estimated_gps_data if self._estimator else self.data

    def message_handler(self, message):
        logging.debug(f"new pubsub on {self.channel}: {message}")
        fields = [
            "timestamp",
            "trip_id",
            # gps_data
            "latitude",
            "longitude",
            "speed",
            "bearing",
        ]
        timestamp, trip_id, *gps_redis_data = self.redis.hmget(self.key, fields)
        # ensure vehicle_id is the same, as expected
        assert self.vehicle_id == message.get(
            "data"
        ), f"{self.vehicle_id=} != {message.get('data')=}"
        self._timestamp = timestamp
        try:
            self.data = GPSData(
                latitude=gps_redis_data[0],
                longitude=gps_redis_data[1],
                speed=gps_redis_data[2],
                heading=gps_redis_data[3],
            )
            if self._estimator:
                self._estimator.update(
                    self.data,
                    self.timestamp,
                )
            else:
                logging.debug(f"Estimator not found for Agency: {self.agency_name}")
        except ValueError as validation_error:
            logging.error(f"Unable to set GPSData from redis: {validation_error}")

        if self.trip_id != trip_id:
            logging.info(f"trip_id changed from {self.trip_id} to {trip_id}")
            self.trip_id = trip_id
        logging.info(
            f"{datetime.now().ctime()}: new vehicle_position from {self.timestamp.ctime()}"
        )
        logging.debug(
            f"message latency [sec]: {(datetime.now() - self.timestamp).total_seconds():.3f}"
        )


class TripSubscriber(AWSRedisEntitySubscriber):
    """Class to get the most recent `trip_update` data in a background thread

    watches for pubsub `new_trip_update` messages, then gets `trip_update` hash set to
    get the timestamp and ensure vehicle_id is as expected

    Eventually there will be other functionality like checking schedule adherence, and
    this will also require further development around the multiple StopTimeUpdates

    `timestamp`: timestamp in trip_update
    `vehicle_id`: vehicle_id references in trip_update

    Args:
        agency_name (str):
            used to namespace agency data within redis
        trip_id (str):
            trip_id used to identify trip_update instance
        vehicle_id (str):
            (optional) vehicle_id used to ensure vehicle_id referenced in trip_update
            does not change. If not provided, it sets it after receiving the first data
    """

    def __init__(self, agency_name, trip_id, vehicle_id=None, **kwargs):
        key = f"trip_update:{trip_id}"
        self._timestamp = None
        self.trip_id = trip_id
        self.vehicle_id = vehicle_id
        super().__init__(agency_name, key, **kwargs)

    @property
    def timestamp(self):
        return (
            datetime.fromtimestamp(float(self._timestamp)) if self._timestamp else None
        )

    def message_handler(self, message):
        logging.debug(f"new pubsub on {self.channel}: {message}")
        fields = ["timestamp", "vehicle_id"]
        timestamp, vehicle_id = self.redis.hmget(self.key, fields)
        self._timestamp = timestamp
        self.data = None
        self.vehicle_id = self.vehicle_id or vehicle_id
        assert self.vehicle_id == vehicle_id
        logging.info(
            f"{datetime.now().ctime()}: new trip_update from {self.timestamp.ctime()}"
        )
        logging.debug(
            f"message latency [sec]: {(datetime.now() - self.timestamp).total_seconds():.3f}"
        )
