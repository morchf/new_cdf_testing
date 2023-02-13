import json
import logging
import os
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, Optional

import boto3
import sqlalchemy
from gtt.service.asset_library import AssetLibraryAPI
from gtt.service.schedule_adherence import (
    AuroraClient,
    ScheduleAdherenceService,
    StaticGtfsService,
)
from redis import Redis
from redis.client import PubSubWorkerThread
from sqlalchemy.pool import NullPool

from gtt.data_model.schedule_adherence import RedisChannel, VehiclePosition
from gtt.data_model.schedule_adherence.static_gtfs import StaticGtfsChannel

logging.getLogger().setLevel(logging.INFO)


class VehiclePositionsChannel(RedisChannel):
    channel_format = "{agency_name}:{channel_id}:{vehicle_id}"

    @classmethod
    def cache(cls, **kwargs):
        return cls.channel(channel_kwargs={**kwargs, "channel_id": "vehicle_position"})

    @classmethod
    def new(cls, **kwargs):
        return cls.channel(
            channel_kwargs={**kwargs, "channel_id": "new_vehicle_position"}
        )


class ScheduleAdherenceManager:
    _vehicle_positions_thread: PubSubWorkerThread
    _schedule_adherence_service: ScheduleAdherenceService
    _redis: Redis
    _agency_id: str

    def __init__(
        self,
        redis: Redis,
        agency_name: str,
        agency_id: str,
        schedule_adherence_service: ScheduleAdherenceService,
        update_frequency: Optional[int] = 15,
    ):
        self._agency_name = agency_name
        self._agency_id = agency_id
        self._redis = redis
        self._schedule_adherence_service = schedule_adherence_service
        self._update_frequency = update_frequency

        # Handle vehicle positions
        logging.info(
            f"Subscribing to vehicle positions: {VehiclePositionsChannel.new(agency_name=agency_name)}"
        )
        pubsub = redis.pubsub()
        pubsub.psubscribe(
            **{
                VehiclePositionsChannel.new(
                    agency_name=agency_name
                ): self._handle_new_vehicle_position
            }
        )
        self._vehicle_positions_thread = pubsub.run_in_thread(
            sleep_time=60, daemon=True
        )

    def _handle_new_vehicle_position(self, msg: Dict[str, Any]):
        vehicle_id = VehiclePositionsChannel.parse(msg["channel"])["vehicle_id"]
        logging.info(f"New vehicle position: {vehicle_id}")

        cached_vehicle_position = self._redis.hgetall(
            VehiclePositionsChannel.cache(
                agency_name=self._agency_name, vehicle_id=vehicle_id
            ),
        )

        if cached_vehicle_position == {}:
            logging.error(f"No cached vehicle position: {vehicle_id}")
            return

        try:
            vehicle_position = VehiclePosition(
                **{k.decode(): v.decode() for k, v in cached_vehicle_position.items()}
            )
        except Exception as e:
            logging.error(f"Failed to parse cached vehicle position {vehicle_id}: {e}")
            logging.error(cached_vehicle_position)
            return

        # Ignore if updated recently
        cached_schedule_status = self._schedule_adherence_service.get_schedule_status(
            agency_id=self._agency_id,
            trip_id=vehicle_position.trip_id,
            vehicle_id=vehicle_id,
        )
        if (
            cached_schedule_status is not None
            and cached_schedule_status.next_update is not None
            and (
                (
                    cached_schedule_status.next_update - vehicle_position.timestamp
                ).seconds
                > self._update_frequency
                # May also check for proximity to next stop
            )
        ):
            logging.info(f"Keeping cached value: {vehicle_id}")
            return

        # Update schedule status
        self._schedule_adherence_service.update_schedule_status(
            agency_id=self._agency_id, vehicle_position=vehicle_position
        )

    def invalidate(self, *_, **__):
        logging.info("Received request to invalidate static GTFS")
        self._schedule_adherence_service.invalidate(agency_id=self._agency_id)

    def stop(self, *_, **__):
        self._vehicle_positions_thread.stop()


def main(**kwargs):
    parser = ArgumentParser(
        description="Monitor vehicle positions to calculate trip delay"
    )
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=int, help="port for redis endpoint")

    parser.add_argument("--aurora-secret-name", type=int, help="Aurora connection info")

    parser.add_argument("--region-name", type=str, help="Region for CDF group path")
    parser.add_argument("--agency-name", type=str, help="Agency for CDF group path")
    parser.add_argument("--asset-lib-url", type=str, help="URL to Asset Library API")
    parser.add_argument("--agency-id", type=str, help="Agency ID from CDF")

    parser.add_argument("--local-development", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")

    args, _ = parser.parse_known_args(namespace=Namespace(**kwargs))

    logging.info("Starting service")

    redis_url = args.redis_url or os.getenv("REDIS_URL")
    redis_port = args.redis_port or int(os.getenv("REDIS_PORT"))

    logging.info(f"Connecting to Redis instance: {redis_url}:{redis_port}")

    redis = Redis(redis_url, redis_port)
    pubsub = redis.pubsub()

    logging.info("Connected to Redis")

    # Use existing agency ID or pull from asset library
    agency_id = args.agency_id or os.getenv("AGENCY_ID")
    region_name = args.region_name or os.getenv("REGION_NAME")
    agency_name = args.agency_name or os.getenv("AGENCY_NAME")

    if agency_id is None:

        asset_lib_url = args.asset_lib_url or os.getenv("ASSET_LIBRARY_URL") or None

        asset_lib_api = AssetLibraryAPI(asset_lib_url)
        agency = asset_lib_api.get_agency(region_name, agency_name)

        agency_id = agency.unique_id.lower()

    logging.info(f"Running for {agency_id=}")

    # Aurora
    secretsmanager = boto3.client("secretsmanager")

    response = secretsmanager.get_secret_value(
        SecretId=args.aurora_secret_name or os.getenv("AURORA_SECRET_NAME")
    )
    secret_dict = json.loads(response["SecretString"])

    host = secret_dict["host"]
    username = secret_dict["username"]
    password = secret_dict["password"]
    port = secret_dict["port"]

    gtfs_conn = f"postgresql://{username}:{password}@{host}:{port}/gtfs"
    aurora_engine = sqlalchemy.create_engine(gtfs_conn, poolclass=NullPool)

    sql_client = AuroraClient(aurora_engine)

    # Services
    logging.info("Starting manager")

    static_gtfs_service = StaticGtfsService(sql_client)
    schedule_adherence_service = ScheduleAdherenceService(redis, static_gtfs_service)

    schedule_adherence_manager = ScheduleAdherenceManager(
        redis,
        agency_name=agency_name,
        agency_id=agency_id,
        schedule_adherence_service=schedule_adherence_service,
    )

    # Listen for static GTFS invalidations
    static_gtfs_invalidate_channel = StaticGtfsChannel.invalidate(agency_id=agency_id)
    logging.info(
        f"Subscribing for static GTFS invalidation updates: {static_gtfs_invalidate_channel}"
    )
    pubsub.psubscribe(
        **{static_gtfs_invalidate_channel: schedule_adherence_manager.invalidate}
    )
    pubsub.run_in_thread(sleep_time=60)


if __name__ == "__main__":
    main()
