from tsp_gtfs_realtime import (
    AWSConfig,
    VehicleSubscriber,
    TripSubscriber,
    CDFConfig,
    CDFClient,
)

import os
from datetime import datetime
import logging
import pause

from argparse import ArgumentParser


def main():
    parser = ArgumentParser(
        description="Create subscriber for trip and related vehicle data to send RT Radio Messages"
    )
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=str, help="port for redis endpoint")
    parser.add_argument(
        "--agency-id",
        type=str,
        help="agencyId of Agency entity in CDF",
    )
    parser.add_argument(
        "--trip-id",
        type=str,
        help="GTFS Realtime trip_id to subscribe to",
    )
    parser.add_argument(
        "--vehicle-id",
        type=str,
        help="""(optional) GTFS Realtime vehicle_id to subscribe to.
        If not provided, vehicle_id of the first trip_update is used""",
    )
    parser.add_argument(
        "--cdf-unique-id",
        type=str,
        help="uniqueId of DeviceIntegration entity in CDF.",
    )
    parser.add_argument(
        "--rt-radio-message-rate",
        type=float,
        default=1.0,
        dest="rt_radio_msg_rate",
        help="time in seconds between each RT Radio Message",
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
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.timeout:
        raise NotImplementedError

    # get from command line args or environment variables (or default)
    verbose_logging = args.verbose or os.environ.get("VERBOSE_LOGGING")
    redis_url = args.redis_url or os.environ.get("REDIS_URL") or "localhost"
    redis_port = args.redis_port or os.environ.get("REDIS_PORT") or 6379
    agency_id = args.agency_id or os.environ.get("AGENCY_ID")
    trip_id = args.trip_id or os.environ.get("TRIP_ID")
    vehicle_id = args.vehicle_id or os.environ.get("VEHICLE_ID")
    cdf_unique_id = args.cdf_unique_id or os.environ.get("CDF_UNIQUE_ID")
    rt_radio_msg_rate = args.rt_radio_msg_rate or os.environ.get("RT_RADIO_MSG_RATE")

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    logging.info(f"Starting new trip manager: {vars(args)}")

    aws_cfg = AWSConfig(
        local_development=True,
        redis_url=redis_url,
        redis_port=redis_port,
    )
    logging.info(f"{aws_cfg=}")
    # trip_subscriber asserts that the vehicle_id does not change once set
    trip_subscriber = TripSubscriber(agency_id, trip_id, vehicle_id, config=aws_cfg)

    # if vehicle_id not provided, wait for it to be retrieved by trip_subscriber
    while not trip_subscriber.vehicle_id:
        # ToDo: timeout if needed, or maybe make TripSubscriber handle waiting/timeout
        logging.info("waiting for first trip_update message to get vehicle_id")
        pause.seconds(1)

    # vehicle_subscriber to get gps_data data for related vehicle_id
    vehicle_subscriber = VehicleSubscriber(
        agency_id,
        trip_subscriber.vehicle_id,
        redis=trip_subscriber.redis,
        config=aws_cfg,
    )

    # ToDo: use given agency_id instead of querying
    if cdf_unique_id:
        cdf_cfg = CDFConfig(
            local_development=True,
            redis=trip_subscriber.redis,
        )
        cdf_client = CDFClient(cdf_cfg)

    rt_radio_msg_count = 0
    timestamps = []
    trip_timestamps = []
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

            # use latest gps_data to send RT Radio Message
            if cdf_unique_id:
                logging.debug(f"sending: {vehicle_subscriber.gps_data}")
                cdf_client.update(cdf_unique_id, vehicle_subscriber.gps_data)
                age = (datetime.now() - vehicle_subscriber.timestamp).total_seconds()
                logging.info(f"sent RT Radio Message with {age:.0f}s old data")
                rt_radio_msg_count += 1

            if args.get_update_frequency:
                prev_timestamp = timestamps[-1] if timestamps else None
                # don't append if equal or both None (None != None evaluates to false)
                if vehicle_subscriber.timestamp != prev_timestamp:
                    timestamps.append(vehicle_subscriber.timestamp)
                prev_trip_timestamp = trip_timestamps[-1] if trip_timestamps else None
                if trip_subscriber.timestamp != prev_trip_timestamp:
                    trip_timestamps.append(trip_subscriber.timestamp)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
        pass
    finally:
        gps_data_count = vehicle_subscriber.data_count
        trip_update_count = trip_subscriber.data_count
        if not gps_data_count:
            logging.info("never received any new_vehicle_position messages")
            logging.info(f"received {trip_update_count} new_trip_update messages")
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
        logging.info(f"got {trip_update_count} updates")
        logging.info(f"sent {total_num_messages} RT Radio Messages")
        if args.get_update_frequency:
            # find average period if more than one timestamp, else nan
            avg_period = (
                ((timestamps[-1] - timestamps[0]) / len(timestamps[1:])).total_seconds()
                if len(timestamps) > 1
                else float("nan")
            )
            logging.info(f"avg time between vehicle update: {avg_period:.1f} seconds")
            avg_trip_period = (
                (
                    (trip_timestamps[-1] - trip_timestamps[0])
                    / len(trip_timestamps[1:])
                ).total_seconds()
                if len(trip_timestamps) > 1
                else float("nan")
            )
            logging.info(f"avg time between trip update: {avg_trip_period:.1f} seconds")


if __name__ == "__main__":
    main()
