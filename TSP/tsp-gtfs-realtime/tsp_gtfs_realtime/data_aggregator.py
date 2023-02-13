import logging
import os
import signal
import sys
import threading
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Dict, List, Tuple

import boto3
import pandas as pd
import pause
from gtt.service.asset_library import AssetLibraryAPI

from tsp_gtfs_realtime.core.aws import AWSRedisEntitySubscriber
from tsp_gtfs_realtime.core.aws import Config as AWSConfig


# need to override init for better control over pubsub
class AWSRedisPatternSubscriber(AWSRedisEntitySubscriber):
    def __init__(self, agency_name, patterns=None, **kwargs):
        super(AWSRedisEntitySubscriber, self).__init__(**kwargs)
        self.pubsub = self.redis.pubsub()

        self.agency_name = agency_name
        self.patterns = [
            f"{self.agency_name}:{p}"
            for p in (patterns if not isinstance(patterns, str) else [patterns])
        ]

        # shared lock, for thread-safe properties
        self._data_lock = threading.Lock()

        # keep track of the time last updated, and whether it has been accessed yet
        self.data_last_updated = None
        self.has_fresh_data = False
        self.data_count = 0

        # subscribe to each pattern with same handler to run in background
        logging.info(f"subscribing to {self.patterns}")
        self.pubsub.psubscribe(**{p: self.message_handler for p in self.patterns})
        self.pubsub.check_health()
        # start subscriber thread as daemon to stop along with main thread
        self._pubsub_thread = self.pubsub.run_in_thread(sleep_time=60, daemon=True)


class AggregationSubscriber(AWSRedisPatternSubscriber):
    """Class to aggregate data in a background thread

    watches for pubsub `new_vehicle_position` and `new_trip_update` messages, then gets
    their corresponding hash set and appends it to a dataframe

    `data`: lists of values to aggregate

    `pop()` -> (pd.DataFrame, pd.DataFrame):
        returns the current aggregation and resets them to be empty

    Args:
        agency_name (str):
            used to namespace agency data within redis
        vehicles (List[str]):
            (optional) subset of vehicle_ids to save
        trips (List[str]):
            (optional) subset of trip_ids to save
    """

    vehicle_position_fields = [
        "entity_id",
        "timestamp",
        "current_stop_sequence",
        "stop_id",
        "current_status",
        "congestion_level",
        "occupancy_status",
        "vehicle_id",
        "vehicle_label",
        "license_plate",
        "latitude",
        "longitude",
        "bearing",
        "odometer",
        "speed",
        "trip_id",
        "route_id",
        "trip_direction_id",
        "trip_start_time",
        "trip_start_date",
        "schedule_relationship",
    ]
    # ToDo: handle stop_time_updates
    trip_update_fields = [
        "timestamp",
        "delay",
        "trip_id",
        "route_id",
        "trip_direction_id",
        "trip_start_time",
        "trip_start_date",
        "schedule_relationship",
        "vehicle_id",
        "vehicle_label",
        "license_plate",
    ]

    def __init__(
        self,
        agency_name,
        vehicles=None,
        trips=None,
        **kwargs,
    ):
        patterns = ("new_vehicle_position:*", "new_trip_update:*")
        self._timestamp = None

        # optionally restrict the subset of vehicles/trips to save
        self.vehicles = set(vehicles) if vehicles else None
        self.trips = set(trips) if trips else None

        # lists to store aggregated dicts
        self._vehicle_positions = []
        self._trip_updates = []

        super().__init__(agency_name, patterns=patterns, **kwargs)

    # ToDo: remove these since append doesn't use the setter and is already atomic
    @property
    def vehicle_positions(self) -> List[Dict]:
        """Thread-safe accessor"""
        # wait for handler thread to unlock if setting new data
        with self._data_lock:
            return self._vehicle_positions

    @vehicle_positions.setter
    def vehicle_positions(self, value):
        with self._data_lock:
            self._vehicle_positions = value
            self.data_count += 1
            self.data_last_updated = datetime.now(timezone.utc)

    @property
    def trip_updates(self) -> List[Dict]:
        """Thread-safe accessor"""
        # wait for handler thread to unlock if setting new data
        with self._data_lock:
            return self._trip_updates

    @trip_updates.setter
    def trip_updates(self, value):
        with self._data_lock:
            self._trip_updates = value
            self.data_count += 1
            self.data_last_updated = datetime.now(timezone.utc)

    def pop(self) -> Tuple[List[Dict], List[Dict]]:
        """Get the aggregated vehicle_positions and trip_updates and reset batch

        Returns:
            ([dict], [dict]): lists of each vehicle_position/trip_update collected
        """
        self.has_fresh_data = False
        vehicle_positions, self.vehicle_positions[:] = self.vehicle_positions[:], []
        trip_updates, self.trip_updates[:] = self.trip_updates[:], []
        return vehicle_positions, trip_updates

    def message_handler(self, message):
        logging.debug(f"new pubsub: {message}")
        value_type, value_id = message["channel"].split(":")[-2:]
        if value_type == "new_vehicle_position":
            self.has_fresh_data = True
            if self.vehicles and value_id not in self.vehicles:
                logging.debug(f"got vehicle not in list: {message=}")
                return
            key = f"{self.agency_name}:vehicle_position:{value_id}"
            value = self.redis.hmget(key, self.vehicle_position_fields)
            self.vehicle_positions.append(value)
            logging.debug(f"appending vehicle_position: {value}")
        elif value_type == "new_trip_update":
            self.has_fresh_data = True
            if self.trips and value_id not in self.trips:
                logging.debug(f"got trip not in list: {message=}")
                return
            key = f"{self.agency_name}:trip_update:{value_id}"
            value = self.redis.hmget(key, self.trip_update_fields)
            self.trip_updates.append(value)
            logging.debug(f"appending trip_update: {value}")
        else:
            logging.warning(f"pattern not handled: {message=}")


def main():
    parser = ArgumentParser(
        description="Create subscriber for vehicle data to send RT Radio Messages"
    )
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=str, help="port for redis endpoint")
    parser.add_argument("--region-name", type=str, help="Region for CDF group path")
    parser.add_argument("--agency-name", type=str, help="Agency for CDF group path")
    parser.add_argument(
        "--vehicle-list",
        type=str,
        nargs="?",
        const=",",
        help="comma-delimited subset of vehicles. if not provided, all vehicles are persisted. Can be empty/None",
    )
    parser.add_argument(
        "--trip-list",
        type=str,
        nargs="?",
        const=",",
        help="comma-delimited subset of trips. if not provided, all trips are persisted. Can be empty/None",
    )
    parser.add_argument(
        "--batch-rate",
        type=int,
        help="time in minutes to group messages within a bucket. Default is 15",
    )
    parser.add_argument("--local-development", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    # get from command line args or environment variables (or default)
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    redis_url = args.redis_url or os.environ.get("REDIS_URL") or "localhost"
    redis_port = args.redis_port or os.environ.get("REDIS_PORT") or 6379
    region_name = args.region_name or os.environ.get("REGION_NAME")
    agency_name = args.agency_name or os.environ.get("AGENCY_NAME")
    vehicle_list = (
        [vehicle for vehicle in args.vehicle_list.split(",") if vehicle]
        if args.vehicle_list is not None
        else [vehicle for vehicle in os.environ["VEHICLE_LIST"].split(",") if vehicle]
        if "VEHICLE_LIST" in os.environ
        else None
    )
    trip_list = (
        [trip for trip in args.trip_list.split(",") if trip]
        if args.trip_list is not None
        else [trip for trip in os.environ["TRIP_LIST"].split(",") if trip]
        if "TRIP_LIST" in os.environ
        else None
    )
    batch_rate = args.batch_rate or float(os.environ.get("BATCH_RATE", 15.0))

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    logging.info(
        f"Starting new data aggregator: {verbose_logging=}, {redis_url=}, "
        f"{redis_port=}, {region_name=}, {agency_name=}, {vehicle_list=}, {trip_list=}, {batch_rate=}"
    )

    aws_cfg = AWSConfig(
        local_development=args.local_development,
        redis_url=redis_url,
        redis_port=redis_port,
    )
    logging.info(f"{aws_cfg=}")
    aggregation_subscriber = AggregationSubscriber(
        agency_name, vehicle_list, trip_list, config=aws_cfg
    )

    if not args.local_development:
        bucket_name = f"gtfs-realtime-{os.environ['AWS_ENVIRONMENT']}"
        bucket = boto3.resource("s3").Bucket(bucket_name)
        # ensure bucket exists by checking that its creation_date is not None
        assert bucket.creation_date, f"s3 bucket {bucket_name} does not exist"

    # ToDo: make this general by getting all agencies at once
    # get agency unique_id from Asset Library to use for folder name
    agency_id = AssetLibraryAPI().get_agency(region_name, agency_name).unique_id

    class SignalHandler:
        """registers double-acting signal handler

        1st occurrence sets a flag, `SignalHandler.signal_received` to be handled later
        2nd occurrence calls `sys.exit()`

        Args:
            signal_num (signal.Signals, optional):
                Signal to handle. Defaults to signal.SIGINT
        """

        def __init__(self, signal_num: signal.Signals = signal.SIGINT):
            self.signal_received = False
            self.name = signal_num.name
            signal.signal(signal_num, self.handler)

        def handler(self, signal_num, frame):
            logging.debug(f"{self.name} handler called with {signal_num=}, {frame=}")
            # if first signal received, exit after current loop iteration
            if not self.signal_received:
                logging.info(f"{self.name} received, exiting after main loop")
                self.signal_received = True
            # if a second signal received, explicitly exit
            else:
                logging.info(f"2nd {self.name} received, exiting now")
                sys.exit(1)

    interrupt_handler = SignalHandler(signal.SIGINT)
    next_batch_time = datetime.now(timezone.utc).replace(microsecond=0)
    next_batch_time += timedelta(minutes=batch_rate)

    logging.info("starting main loop, waiting for first batch")
    while not interrupt_handler.signal_received:
        # start loop every `batch_rate` minutes
        pause.until(next_batch_time)
        vehicle_positions_filepath, trip_updates_filepath = (
            f"{message_name}/"
            f"agency_id={agency_id}/"
            f"utc_date={next_batch_time.date()}/"
            f"{next_batch_time.isoformat()}.parquet"
            for message_name in ["vehicle_positions", "trip_updates"]
        )
        next_batch_time += timedelta(minutes=batch_rate)

        if not aggregation_subscriber.has_fresh_data:
            logging.info("no data in batch")
            continue

        # get aggregated data and reset
        vehicle_positions, trip_updates = aggregation_subscriber.pop()

        if args.local_development:
            logging.info(
                f"got {len(vehicle_positions)} vehicle_positions and {len(trip_updates)} trip_updates. Not uploading due to local_development",
            )
            continue

        # process to a parquet file and upload to s3 (without saving to the file system)
        if vehicle_positions:
            with BytesIO() as fp:
                pd.DataFrame(
                    vehicle_positions,
                    columns=aggregation_subscriber.vehicle_position_fields,
                ).to_parquet(fp, index=False)
                bucket.put_object(Key=vehicle_positions_filepath, Body=fp.getvalue())
                logging.info(f"saved {len(vehicle_positions)} vehicle_positions")
        else:
            logging.info("no vehicle_positions in batch")

        if trip_updates:
            with BytesIO() as fp:
                pd.DataFrame(
                    trip_updates, columns=aggregation_subscriber.trip_update_fields
                ).to_parquet(fp, index=False)
                bucket.put_object(Key=trip_updates_filepath, Body=fp.getvalue())
                logging.info(f"saved {len(trip_updates)} trip_updates")
        else:
            logging.info("no trip_updates in batch")

    logging.info("End of main loop, exiting")


if __name__ == "__main__":
    main()
