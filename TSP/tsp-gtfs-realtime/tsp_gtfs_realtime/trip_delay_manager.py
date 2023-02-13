import logging
import os
from argparse import ArgumentParser
from datetime import datetime
from typing import Any, Dict, Optional

from gtt.service.asset_library import AssetLibraryAPI
from gtt.service.feature_persistence import FeaturePersistenceAPI
from pydantic import BaseModel, PrivateAttr, ValidationError
from redis import Redis


class TripDelayMessage(BaseModel):
    trip_id: str
    vehicle_id: str
    delay: float


class SetTSPEnabledMessage(BaseModel):
    vehicle_id: str
    enabled: bool


# ToDo: Replace with BaseSettings and @usesources wrapper
class Settings(BaseModel):
    redis_url: str
    redis_port: int
    region_name: str
    agency_name: str
    asset_lib_url: Optional[str] = None
    feature_persistence_url: Optional[str] = None
    verbose_logging: bool

    _redis: Optional[Redis] = PrivateAttr(default=None)
    _agency_id: Optional[str] = PrivateAttr(default=None)
    _delay_threshold: Optional[float] = PrivateAttr(default=None)

    @property
    def redis(self) -> Redis:
        if not self._redis:
            self._redis = Redis(host=self.redis_url, port=self.redis_port)
            self._redis.ping()
        return self._redis

    @property
    def agency_id(self) -> Redis:
        if not self._agency_id:
            asset_lib_api = AssetLibraryAPI(self.asset_lib_url)
            agency = asset_lib_api.get_agency(self.region_name, self.agency_name)
            self._agency_id = agency.unique_id.lower()
        return self._agency_id

    @property
    def delay_threshold(self) -> float:
        if not self._delay_threshold:
            try:
                fp_api = FeaturePersistenceAPI(self.feature_persistence_url)
                asm_feature: Dict[str, Any] = fp_api.get_feature(
                    agency_id=self.agency_id, feature_name="tsp-asm"
                )
                self._delay_threshold = float(asm_feature["trip_delay_threshold"])
            except Exception as e:
                logging.error(f"Failed to load delay threshold: {e}")
                logging.error("Using default value of 0")

                self._delay_threshold = 0

        return self._delay_threshold

    def configure_logging(self):
        log_level = logging.DEBUG if self.verbose_logging else logging.INFO
        logging.basicConfig(level=log_level, format="%(message)s")
        logging.getLogger().setLevel(log_level)

    @classmethod
    def from_cli_and_env(cls) -> "Settings":
        parser = ArgumentParser(
            description="Keep track of transit vehicle delay and enable/disable TSP accordingly"
        )
        parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
        parser.add_argument("--redis-port", type=int, help="port for redis endpoint")
        parser.add_argument("--region-name", type=str, help="Region for CDF group path")
        parser.add_argument("--agency-name", type=str, help="Agency for CDF group path")

        parser.add_argument(
            "--asset-lib-url", type=str, help="URL to Asset Library API"
        )
        parser.add_argument(
            "--feature-persistence-url", type=str, help="URL to Feature Persistence API"
        )

        parser.add_argument("--local-development", action="store_true")
        parser.add_argument("--verbose", "-v", action="store_true")

        args = parser.parse_args()

        return cls(
            redis_url=args.redis_url or os.getenv("REDIS_URL") or "localhost",
            redis_port=args.redis_port or os.getenv("REDIS_PORT") or 6379,
            region_name=args.region_name or os.getenv("REGION_NAME"),
            agency_name=args.agency_name or os.getenv("AGENCY_NAME"),
            asset_lib_url=args.asset_lib_url or os.getenv("ASSET_LIBRARY_URL") or None,
            fp_url=(
                args.feature_persistence_url
                or os.getenv("FEATURE_PERSISTENCE_URL")
                or None
            ),
            verbose_logging=args.verbose or "VERBOSE_LOGGING" in os.environ or False,
        )


def main():
    settings = Settings.from_cli_and_env()
    settings.configure_logging()
    logging.info(f"Starting new trip delay manager: {settings=}")

    redis = settings.redis
    trip_delay_channel = f"tsp_in_cloud:new_trip_delay:{settings.agency_id}:*"

    set_tsp_channel_base = f"tsp_in_cloud:new_tsp_enabled:{settings.agency_id}"
    tsp_enabled_key = f"tsp_in_cloud:tsp_enabled:{settings.agency_id}"

    def handle_new_delay(msg: Dict[str, str]):
        try:
            trip_delay_msg = TripDelayMessage.parse_raw(msg["data"].decode())
        except ValidationError as e:
            logging.error(
                f"Problem deserializing trip delay message from {msg['channel']} {msg['data']}\n{e}"
            )
            return

        logging.info(
            f"Received new trip delay from vehicle {trip_delay_msg.vehicle_id} at: {datetime.now()}"
        )
        logging.debug(f"\t{trip_delay_msg=}")

        # Do nothing if vehicle isn't supported
        if not redis.sismember(
            f"tsp_in_cloud:supported_vehicle_ids:{settings.agency_id}",
            trip_delay_msg.vehicle_id,
        ):
            logging.info(
                f"Unsupported Vehicle: {trip_delay_msg.vehicle_id} (not in Asset Library)"
            )
            return

        enabled = trip_delay_msg.delay > settings.delay_threshold

        set_tsp_channel = f"{set_tsp_channel_base}:{trip_delay_msg.vehicle_id}"
        set_tsp_msg = SetTSPEnabledMessage(
            vehicle_id=trip_delay_msg.vehicle_id, enabled=enabled
        )
        logging.debug(f"Set and Publishing to: {set_tsp_channel}\n{set_tsp_msg=}")

        redis.set(
            f"tsp_in_cloud:tsp_enabled:{settings.agency_id}:{trip_delay_msg.vehicle_id}",
            set_tsp_msg.json(),
        )
        # Publish 'vehicle_id' to help identify message
        redis.publish(set_tsp_channel, trip_delay_msg.vehicle_id)
        if enabled:
            redis.sadd(tsp_enabled_key, trip_delay_msg.vehicle_id)
        else:
            redis.srem(tsp_enabled_key, trip_delay_msg.vehicle_id)

    pubsub = redis.pubsub()
    pubsub.psubscribe(**{trip_delay_channel: handle_new_delay})
    logging.info(f"Subscribing to: {trip_delay_channel}")
    pubsub.run_in_thread(sleep_time=60)


if __name__ == "__main__":
    main()
