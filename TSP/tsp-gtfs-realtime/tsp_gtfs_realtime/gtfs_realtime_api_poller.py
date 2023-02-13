import logging
import os
import time
from argparse import ArgumentParser

from gtt.service.asset_library import AssetLibraryAPI

from gtt.data_model.rt_radio_message import GPSData
from tsp_gtfs_realtime.core.aws import AWSRedisBase
from tsp_gtfs_realtime.core.aws import Config as AWSConfig
from tsp_gtfs_realtime.core.gtfs_realtime import (
    GTFSRealtimeAPIPoller,
    GTFSRealtimeConfig,
)


class AWSPublisher(AWSRedisBase):
    """A class to publish the updated GTFS Realtime data

    Args:
        config (AWSConfig): configuration object for initialize AWS connections
        agency_name (str): used to namespace agency data within redis
        vehicle_list (list): optional subset of vehicles to publish
        trip_list (list): optional subset of trips to publish
    """

    def __init__(
        self,
        aws_config: AWSConfig,
        agency_name: str,
        vehicle_list: list = None,
        trip_list: list = None,
        publish_stop_time_updates: bool = False,
    ):
        self.agency_name = agency_name

        # ToDo: get list of vehicles/trips from CDF
        self.vehicle_list = vehicle_list
        self.trip_list = trip_list

        self.last_updated = 0
        self.agency_channel_name = f"{self.agency_name}:new_agency_data"
        self.last_updated_key = f"{self.agency_name}:last_updated"

        self.vehicle_set_key = f"{self.agency_name}:vehicle_ids"
        self.vehicle_position_key_base = f"{self.agency_name}:vehicle_position"
        self.vehicle_channel_name_base = f"{self.agency_name}:new_vehicle_position"
        self.gps_channel_name_base = f"{self.agency_name}:new_gps_data"

        self.trip_set_key = f"{self.agency_name}:trip_ids"
        self.trip_update_key_base = f"{self.agency_name}:trip_update"
        self.trip_channel_name_base = f"{self.agency_name}:new_trip_update"
        self.publish_stop_time_updates = publish_stop_time_updates

        super().__init__(config=aws_config)

    def update_vehicle_position(self, vehicle_id: str, fields: dict):
        # filter vehicles not in self.vehicle_list (if None, publish all vehicles)
        if self.vehicle_list is not None and vehicle_id not in self.vehicle_list:
            logging.debug(f"{vehicle_id}: not in vehicle_list")
            return
        vehicle_position_key = f"{self.vehicle_position_key_base}:{vehicle_id}"
        prev_update = self.redis.hget(vehicle_position_key, "timestamp")
        # ToDo: Some updates have the same timestamp but different data. a correction?
        if prev_update != fields.get("timestamp"):
            # add to set of vehicles
            self.redis.sadd(self.vehicle_set_key, vehicle_id)
            # update fields for vehicle_id
            self.redis.hset(vehicle_position_key, mapping=fields)
            # publish to alert subscribers to new data for vehicle_id
            vehicle_channel_name = f"{self.vehicle_channel_name_base}:{vehicle_id}"
            self.redis.publish(vehicle_channel_name, vehicle_id)
            try:
                gps_channel_name = f"{self.gps_channel_name_base}:{vehicle_id}"
                gps_data = GPSData(
                    latitude=fields.get("latitude"),
                    longitude=fields.get("longitude"),
                    speed=fields.get("speed"),
                    heading=fields.get("bearing"),
                )
                self.redis.publish(gps_channel_name, gps_data.json())
            except ValueError as validation_error:
                logging.error(f"Could not publish GPSData to Redis: {validation_error}")
        else:
            logging.debug(f"{vehicle_id}: {prev_update} == {fields.get('timestamp')}")

    def update_trip(self, trip_id: str, fields: dict):
        # filter trips not in self.trip_list (if None, publish all trips)
        if self.trip_list is not None and trip_id not in self.trip_list:
            logging.debug(f"{trip_id}: not in trip_list")
            return
        trip_update_key = f"{self.trip_update_key_base}:{trip_id}"
        prev_update = self.redis.hget(trip_update_key, "timestamp")
        if prev_update != fields.get("timestamp"):
            # add to set of trips
            self.redis.sadd(self.trip_set_key, trip_id)
            # separate list of stoptimeupdates from fields
            stop_time_updates = fields.pop("stop_time_updates")
            # update top-level fields for trip_id
            self.redis.hset(trip_update_key, mapping=fields)
            # update each stop_time_update for trip_id
            if self.publish_stop_time_updates:
                for stu_fields in stop_time_updates:
                    trip_stop_time_update_key = (
                        f"{trip_update_key}:{stu_fields['stop_id']}"
                    )
                    self.redis.hset(trip_stop_time_update_key, mapping=stu_fields)
            self.redis.sadd(self.trip_set_key, trip_id)
            # publish to alert subscribers to new data for trip_id
            trip_channel_name = f"{self.trip_channel_name_base}:{trip_id}"
            self.redis.publish(trip_channel_name, trip_id)
        else:
            logging.debug(f"{trip_id}: {prev_update} == {fields.get('timestamp')}")

    def set_last_updated(self, timestamp):
        if timestamp > self.last_updated:
            self.last_updated = timestamp
            self.redis.set(self.last_updated_key, self.last_updated)
            # publish to alert subscribers to any new data
            self.redis.publish(self.agency_channel_name, self.last_updated)


def main():
    parser = ArgumentParser(
        description="Subscribe to gtfs realtime feeds and store with redis/elasticache",
    )
    parser.add_argument("--local-development", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-c", "--config", help="link to config file", metavar="")
    parser.add_argument("--region-name", type=str, help="Region for CDF group path")
    parser.add_argument("--agency-name", type=str, help="Agency for CDF group path")
    parser.add_argument(
        "--vehicle-list",
        type=str,
        nargs="?",
        const=",",
        help="comma-delimited subset of vehicles to publish. if not provided, all vehicles are published. Can be empty/None",
    )
    parser.add_argument(
        "--trip-list",
        type=str,
        nargs="?",
        const=",",
        help="comma-delimited subset of trips to publish. if not provided, all trips are published. Can be empty/None",
    )
    args = parser.parse_args()

    # get from command line args or environment variables
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    config_file = args.config or os.environ.get("CONFIG_FILE")
    region_name = args.region_name or os.environ.get("REGION_NAME")
    agency_name = args.agency_name or os.environ.get("AGENCY_NAME")
    should_query_feature_api = not (
        args.local_development or "QUERY_FEATURE_API" in os.environ
    )
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

    logging.info(
        f"input_args: {verbose_logging=}, {config_file=}, {region_name=}, {agency_name=}, {should_query_feature_api=}, {vehicle_list=}, {trip_list=}"
    )

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    agency_id = AssetLibraryAPI().get_agency(region_name, agency_name).unique_id

    # ToDo: either query AgencyGUID from CDF or just use name (would need to enforce uniqueness in backend)
    gtfs_cfg = GTFSRealtimeConfig.from_inputs(
        agency_id=agency_id,
        should_query_feature_api=should_query_feature_api,
        config_file=config_file,
    )
    logging.info(f"{gtfs_cfg=}")
    gtfs_realtime_api_poller = GTFSRealtimeAPIPoller(gtfs_cfg)

    aws_cfg = AWSConfig(
        local_development=True,
        redis_url=os.environ.get("REDIS_URL") or "localhost",
        redis_port=os.environ.get("REDIS_PORT") or 6379,
    )
    logging.info(f"{aws_cfg=}")
    aws_publisher = AWSPublisher(aws_cfg, agency_name, vehicle_list, trip_list)

    # ToDo: separate threads
    previous_vehicle_positions_feed_time = 0
    previous_trip_updates_feed_time = 0
    while True:
        # update vehicle_positions
        gtfs_realtime_api_poller.poll_vehicle_positions()
        vehicle_positions_feed_time = (
            gtfs_realtime_api_poller.vehicle_positions_last_updated
        )
        if vehicle_positions_feed_time > previous_vehicle_positions_feed_time:
            previous_vehicle_positions_feed_time = vehicle_positions_feed_time
            logging.debug(
                f"{time.ctime()}: got new vehicle_positions feed from {time.ctime(vehicle_positions_feed_time)}"
            )
            # update all vehicles
            for vehicle_id, fields in gtfs_realtime_api_poller.vehicle_positions:
                aws_publisher.update_vehicle_position(vehicle_id, fields)
            aws_publisher.set_last_updated(vehicle_positions_feed_time)
        else:
            logging.debug(
                f"{time.ctime()}: got stale vehicle_positions feed from {time.ctime(vehicle_positions_feed_time)}"
            )
        # update trip_updates
        gtfs_realtime_api_poller.poll_trip_updates()
        trip_updates_feed_time = gtfs_realtime_api_poller.trip_updates_last_updated
        if trip_updates_feed_time > previous_trip_updates_feed_time:
            previous_trip_updates_feed_time = trip_updates_feed_time
            logging.debug(
                f"{time.ctime()}: got new trip_updates feed from {time.ctime(trip_updates_feed_time)}"
            )
            # update all trips
            for trip_id, fields in gtfs_realtime_api_poller.trip_updates:
                aws_publisher.update_trip(trip_id, fields)
            aws_publisher.set_last_updated(trip_updates_feed_time)
        else:
            logging.debug(
                f"{time.ctime()}: got stale trip_updates feed from {time.ctime(trip_updates_feed_time)}"
            )
        if vehicle_positions_feed_time or trip_updates_feed_time:
            aws_publisher.set_last_updated(
                max(vehicle_positions_feed_time, trip_updates_feed_time)
            )


if __name__ == "__main__":
    main()
