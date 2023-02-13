import json
import logging
import os
from argparse import ArgumentParser
from datetime import datetime
from typing import ClassVar, Dict

import pause
from gtt.service.iot_core import IoTCoreService
from redis import Redis

from tsp_gtfs_realtime.core.aws import Config as AWSConfig
from tsp_gtfs_realtime.core.aws import VehicleSubscriber
from tsp_gtfs_realtime.core.estimation import SimplePositionEstimator


class TSPEnabledSubscriber:
    set_tsp_enabled_channel_base: ClassVar[str] = "tsp_in_cloud:new_tsp_enabled:*"

    _is_enabled: bool

    def __init__(self, redis: Redis, vehicle_id: str) -> None:
        self._is_enabled = True
        pubsub = redis.pubsub()
        pubsub.psubscribe(
            **{
                f"{self.set_tsp_enabled_channel_base}:{vehicle_id}": self.handle_set_tsp_enabled
            }
        )
        pubsub.run_in_thread(sleep_time=60, daemon=True)

    def handle_set_tsp_enabled(self, msg: Dict[str, str]):
        logging.debug(f"Handling TSP enable/disable: {msg}")
        self._is_enabled = bool(json.loads(msg["data"])["enabled"])

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled


def main():
    parser = ArgumentParser(
        description="Create subscriber for vehicle data to send RT Radio Messages"
    )
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=str, help="port for redis endpoint")
    parser.add_argument("--region-name", type=str, help="Region for CDF group path")
    parser.add_argument("--agency-name", type=str, help="Agency for CDF group path")
    parser.add_argument(
        "--trip-id",
        type=str,
        help="(optional) GTFS Realtime trip_id to set initially, only for logging.",
    )
    parser.add_argument(
        "--vehicle-id",
        type=str,
        help="GTFS Realtime vehicle_id to subscribe to",
    )
    parser.add_argument(
        "--cdf-device-id",
        type=str,
        help="device_id of IntegrationCom entity in CDF",
    )
    parser.add_argument(
        "--position-estimator",
        type=str,
        choices=[SimplePositionEstimator.__name__, "None"],
        help=f"which position estimator to use between updates, default={SimplePositionEstimator.__name__}",
    )
    parser.add_argument(
        "--rt-radio-message-rate",
        type=float,
        dest="rt_radio_msg_rate",
        help="time in seconds between each RT Radio Message, default=1.0",
    )
    parser.add_argument(
        "--get-update-frequency",
        action="store_true",
        help="note the time difference between vehicle updates",
    )
    parser.add_argument(
        "--num-messages",
        type=int,
        help="the number of RT Radio Messages to send before exiting, default=infinite",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="the max time to wait for data before exiting, default=infinite",
    )
    parser.add_argument("--local-development", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.timeout:
        raise NotImplementedError

    # get from command line args or environment variables (or default)
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    redis_url = args.redis_url or os.environ.get("REDIS_URL") or "localhost"
    redis_port = args.redis_port or os.environ.get("REDIS_PORT") or 6379
    region_name = args.region_name or os.environ.get("REGION_NAME")
    agency_name = args.agency_name or os.environ.get("AGENCY_NAME")
    trip_id = args.trip_id or os.environ.get("TRIP_ID")
    vehicle_id = args.vehicle_id or os.environ.get("VEHICLE_ID")
    position_estimator = (
        None if args.position_estimator == "None" else SimplePositionEstimator()
    )
    cdf_device_id = args.cdf_device_id or os.environ.get("CDF_DEVICE_ID")
    rt_radio_msg_rate = args.rt_radio_msg_rate or float(
        os.environ.get("RT_RADIO_MSG_RATE", 1.0)
    )

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    logging.info(
        f"Starting new vehicle manager: {verbose_logging=}, {redis_url=}, "
        f"{redis_port=}, {region_name=}, {agency_name=}, {trip_id=}, {vehicle_id=}, "
        f"{position_estimator=}, {cdf_device_id=}, {rt_radio_msg_rate=}"
    )

    aws_cfg = AWSConfig(
        local_development=args.local_development,
        redis_url=redis_url,
        redis_port=redis_port,
    )
    logging.info(f"{aws_cfg=}")
    # vehicle_subscriber to get gps_data data for related vehicle_id
    vehicle_subscriber = VehicleSubscriber(
        agency_name,
        vehicle_id,
        trip_id,
        config=aws_cfg,
        estimator=position_estimator,
    )

    tsp_enabled_subscriber = TSPEnabledSubscriber(vehicle_subscriber.redis, vehicle_id)

    iot_core = IoTCoreService(redis=vehicle_subscriber.redis)

    rt_radio_msg_count = 0
    timestamps = []
    start_time = datetime.now()
    next_rt_radio_msg_time = start_time.timestamp()

    # Try to send `num_messages` messages
    try:
        while (not args.num_messages) or rt_radio_msg_count < args.num_messages:
            # start loop every `rt_radio_msg_rate` seconds
            pause.until(next_rt_radio_msg_time)
            next_rt_radio_msg_time += rt_radio_msg_rate

            if not vehicle_subscriber.gps_data:
                logging.info("waiting for first vehicle_position update")
                continue

            # use latest/predicted gps_data to send RT Radio Message
            if cdf_device_id:
                logging.debug(f"sending: {vehicle_subscriber.gps_data}")
                iot_core.update(
                    device_id=cdf_device_id,
                    gps_data=vehicle_subscriber.gps_data,
                    operational=tsp_enabled_subscriber.is_enabled,
                )
                age = (datetime.now() - vehicle_subscriber.timestamp).total_seconds()
                logging.info(
                    f"sent RT Radio Message with {age:.0f}s old data (TSP={'ENABLED' if tsp_enabled_subscriber.is_enabled else 'DISABLED'})"
                )
                rt_radio_msg_count += 1

            if args.get_update_frequency:
                prev_timestamp = timestamps[-1] if timestamps else None
                # don't append if equal or both None (None != None evaluates to false)
                if vehicle_subscriber.timestamp != prev_timestamp:
                    timestamps.append(vehicle_subscriber.timestamp)
    # still exit normally on keyboard interrupt
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
        pass

    gps_data_count = vehicle_subscriber.data_count
    if not gps_data_count:
        logging.info("never received any new_vehicle_position messages")
        return
    # calculate aggregate statistics if we got anything
    logging.info("Calculating aggregate statistics and exiting")
    total_num_messages = (
        f"{rt_radio_msg_count} / {args.num_messages}"
        if args.num_messages
        else str(rt_radio_msg_count)
    )
    total_seconds = (datetime.now() - start_time).total_seconds()
    logging.info(f"got {gps_data_count} updates in {total_seconds:.1f} seconds")
    logging.info(f"sent {total_num_messages} RT Radio Messages")
    if args.get_update_frequency:
        # find average period if more than one timestamp, else nan
        avg_period = (
            ((timestamps[-1] - timestamps[0]) / len(timestamps[1:])).total_seconds()
            if len(timestamps) > 1
            else float("nan")
        )
        logging.info(f"avg time between vehicle update: {avg_period:.1f} seconds")


if __name__ == "__main__":
    main()
