import json
import logging
import os
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import List, Union

import pandas as pd
import pause
import requests
from dateutil import tz

from tsp_gtfs_realtime.core.aws import Config
from tsp_gtfs_realtime.gtfs_realtime_api_poller import AWSPublisher


def dataframe_from_parquet(
    filename: Union[str, Path],
    start_time: pd.Timestamp = None,
    end_time: pd.Timestamp = None,
    time_correction: bool = True,
    begin_with_current_time: bool = True,
    timezone: str = None,
    vehicle_list: List[str] = None,
):
    """preprocess parquet file to return sorted dataframe

    Args:
        filename (str): local parquet file
        start_time (pandas.Timestamp): Optional, minimum timestamp
        end_time (pandas.Timestamp): Optional, maximum timestamp
        time_correction (bool): whether to update timestamps to current, default=True

    Raises:
        FileNotFoundError: unable to find given parquet file
        ValueError: start_time/end_time is not in the time range of the data
    """
    # make sure file exists
    parquet_file = Path(filename).expanduser()
    logging.debug(f"using parquet file: '{parquet_file}'")
    if not parquet_file.is_file():
        raise FileNotFoundError(f"unable to find parquet file: '{filename}'")

    # read parquet file into dataframe
    df = pd.read_parquet(parquet_file)

    df["time"] = pd.to_datetime(df.timestamp, unit="s")

    # make sure provided start_time is in the DatetimeIndex range
    if start_time and not (df.time.min() <= start_time < df.time.max()):
        raise ValueError(
            f"start_time: {start_time} not in the time range of the data: "
            f"[{df.time.min()} : {df.time.max()}]"
        )
    # make sure provided end_time is in the DatetimeIndex range
    if end_time and not (df.time.min() <= end_time < df.time.max()):
        raise ValueError(
            f"end_time: {end_time} not in the time range of the data: "
            f"[{df.time.min()} : {df.time.max()}]"
        )

    if vehicle_list is not None:
        df = df[df["vehicle_id"].isin(vehicle_list)]

    # set start/end time to the earliest/latest update if not provided
    start_time = start_time or df.time.min()
    logging.info(f"setting start time to {start_time}")
    end_time = end_time or df.time.max()
    logging.info(f"setting end time to {end_time}")

    # offset time based on current time
    if time_correction:
        time_offset = pd.Timestamp.now() + pd.Timedelta(5, "sec") - start_time
        logging.info(f"adding {time_offset} to make times current")
        df["time"] = df.time + time_offset
        start_time += time_offset
        end_time += time_offset

    df.index = df.time

    if begin_with_current_time:
        localtz = tz.gettz(timezone)
        start_time_of_day = (
            start_time.to_pydatetime().astimezone(tz=localtz).strftime("%H:%M:%S")
        )

        df = df.between_time(start_time_of_day, "23:59")

    # create columns for expected fields
    assert set(RecordedDataPlayback.fields) == {
        "timestamp",
        "vehicle_id",
        "trip_id",
        "longitude",
        "latitude",
        "speed",
        "bearing",
    }
    # unix timestamps in local timezone
    df["timestamp"] = df.time.apply(lambda x: x.to_pydatetime().timestamp())

    #     df["vehicle_id"] = df.deviceID
    #     df["trip_id"] = df.routeName
    #     df[["longitude", "latitude"]] = pd.DataFrame(
    #         [row["coordinates"] for row in df["loc"].values], index=df.index
    #     )
    #     # mph to m/s
    #     df["speed"] = df.mph * 0.44704
    #     df["bearing"] = df.dir

    rtn_df = df.sort_index()[start_time:end_time][RecordedDataPlayback.fields]
    logging.debug(f"returning {len(rtn_df)/len(df):.3%} of original time range, sorted")
    return rtn_df


class RecordedDataPlayback:
    """A class to simulate the GTFSRealtimeAPIPoller using recorded data

    The source of recorded data is a parquet file, but can be expanded to a csv file, or
    Athena endpoint

    if `polling_rate` is set, updates for the last `polling_rate` seconds are published
    every `polling_rate` seconds. This adds latency similar to actual feed behavior. If
    not set, each subsequent update is sent individually without added latency

    if `playback_speed` is set, a publishing delay is introduced to connect the playback
    time to actual time. If not set, the updates are sent as fast as possible

    if `start_time` is set, recorded data is only sent if it occurs after this time

    if `end_time` is set, recorded data is only sent if it occurs before this time

    if `should_repeat` is True, playback is restarted after reaching the end

    Args:
        source (str): filename or endpoint url
        polling_rate (float): timeslice for grouping updates, default=None
        playback_speed (float): timestamp vs actual time, default=None
        start_time (float | datetime): timestamp or datetime to start, default=None
        end_time (float | datetime): timestamp or datetime to stop, default=None
        should_repeat (float | datetime): repeat once finished, default=False
        time_correction (bool): whether to offset timestamp to current, default=True
    """

    # minimum data needed by VehicleSubscriber
    gps_fields = ["latitude", "longitude", "speed", "bearing"]
    fields = ["timestamp", "vehicle_id", "trip_id", *gps_fields]

    def __init__(
        self,
        source: str,
        polling_rate: float = None,
        playback_speed: float = None,
        start_time: Union[datetime, float] = None,
        end_time: Union[datetime, float] = None,
        should_repeat: bool = False,
        time_correction: bool = True,
        begin_with_current_time: bool = True,
        timezone: str = None,
        vehicle_list: List[str] = None,
    ):
        self.source = source
        self.polling_rate = pd.Timedelta(polling_rate, "sec") if polling_rate else None
        self.playback_speed = playback_speed
        if playback_speed and playback_speed != 1:
            self.playback_speed = 1
            logging.warning("non-unity playback not yet implemented, setting to 1.0")

        self.start_time = pd.to_datetime(start_time)
        if start_time:
            logging.debug(f"interpreting start_time {start_time} as {self.start_time}")
        self.end_time = pd.to_datetime(end_time)
        if end_time:
            logging.debug(f"interpreting end_time {end_time} as {self.end_time}")

        self.should_repeat = should_repeat
        self._repeat_count = 0

        self._vehicle_positions = {}
        self._vehicle_positions_count = 0

        # raise error if source is anything other than local parquet file
        if not self.source.lower().endswith("parquet"):
            raise NotImplementedError("only parquet files are currently supported")
        if self.source.lower().startswith(("http", "s3", "arn", "sfmta")):
            raise NotImplementedError("loading remote resource not yet implemented")

        # pre-process parquet file
        self.df = dataframe_from_parquet(
            self.source,
            self.start_time,
            self.end_time,
            time_correction,
            begin_with_current_time,
            timezone,
            vehicle_list,
        )
        self.start_time, self.end_time = self.df.index.min(), self.df.index.max()
        logging.debug(f"updating times to {self.start_time=}, {self.end_time=}")

    def get_statistics(self, vehicle_list=None):
        # find total update count using full*repeat_count + partial
        full_vehicle_positions_count = (
            -(self.end_time - self.start_time) // -self.polling_rate
            if self.polling_rate
            else len(self.df)
            if self.playback_speed
            else 1
        )
        total_feed_updates = (
            full_vehicle_positions_count * self._repeat_count
            + self._vehicle_positions_count
        )

        # if on repeat iteration, just use whole dataset, else slice to current time
        if self._repeat_count:
            logging.warn("per-vehicle statistics only use first iteration if on repeat")
            df = self.df
        else:
            df = self.df[self.start_time : self.last_updated]

        # per-dataset statistics
        logging.info(f"{total_feed_updates} vehicle_position feed updates")
        logging.info(f"{df.vehicle_id.nunique()} total vehicle_ids")
        logging.info(f"{df.trip_id.nunique()} total trip_ids")
        logging.info(f"{len(df)} total vehicle_positions")

        # per-vehicle statistics
        for vehicle_id, df_vehicle in df.groupby("vehicle_id"):
            if vehicle_list is not None and vehicle_id not in vehicle_list:
                logging.debug(f"skipping summary for vehicle_id: {vehicle_id}")
                continue

            vehicle_rate = df_vehicle.index.to_series().diff()
            total_time = vehicle_rate.sum().round("1s").to_pytimedelta()
            mean_update_time = vehicle_rate.mean().total_seconds()
            median_update_time = vehicle_rate.median().total_seconds()
            pct_under_15s = sum(vehicle_rate < pd.Timedelta(15, "s")) / len(df_vehicle)
            gps_data_fully_populated = df_vehicle[self.gps_fields].notna().values.all()
            timestamps_fully_unique = not df_vehicle.index.duplicated().any()

            logging.info(f"summary for vehicle_id:          {vehicle_id}")
            logging.info(f"  trip_ids:                      {set(df_vehicle.trip_id)}")
            logging.info(f"  vehicle_position update count: {len(df_vehicle)}")
            logging.info(f"  time range:                    {total_time}")
            logging.info(f"  mean update time [sec]:        {mean_update_time:.2f}")
            logging.info(f"  median update time [sec]:      {median_update_time:.2f}")
            logging.info(f"  updates under 15 seconds:      {pct_under_15s:.2%}")
            logging.info(f"  gps_data fully populated:      {gps_data_fully_populated}")
            logging.info(f"  timestamps fully unique:       {timestamps_fully_unique}")

    @property
    def is_done(self):
        """checks for end of data, restarting if `should_repeat`

        if `should_repeat`, the data timestamps are reset instead of returning True

        Returns:
            bool: true if there is no more data
        """
        # data still available in current iteration
        if self.last_updated < self.end_time:
            return False

        if not self.should_repeat:
            return True
        else:
            self._repeat_count += 1
            logging.info(f"resetting and extending playback: {self._repeat_count}")
            self._vehicle_positions = {}
            self._vehicle_positions_count = 0
            # offset dataframe times by total time (+ a second to track) to extend data
            time_offset = self.end_time - self.start_time + pd.Timedelta(1, "sec")
            self.df.index += time_offset
            self.df["timestamp"] += time_offset.total_seconds()
            self.start_time += time_offset
            self.end_time += time_offset
            logging.debug(f"updating times to {self.start_time=}, {self.end_time=}")
            return False

    @property
    def next_poll_time(self):
        # increment time based on vehicle/trip count. If vehicle is polled twice before
        # trip, this ensures the next trip update contains all data until current time
        # return self.last_updated + self.polling_rate
        return (
            self.last_updated + self.polling_rate
            if self.polling_rate
            else (
                # next update time if using playback_speed
                self.df.iloc[[self._vehicle_positions_count]].index[-1]
                if self.playback_speed
                # None, if using neither
                else None
            )
        )

    @property
    def vehicle_positions_last_updated(self):
        return (
            self.start_time + self._vehicle_positions_count * self.polling_rate
            if self.polling_rate
            else (
                # previous update time if using playback_speed
                self.df.iloc[[self._vehicle_positions_count - 1]].index[-1]
                if self.playback_speed
                # end_time, if using neither
                else self.end_time
            )
        )

    last_updated = vehicle_positions_last_updated

    def poll_vehicle_positions(self):
        """create list of tuples representing key, fields for values in time range

        Behavior varies based on usage of polling_rate and/or playback_speed:

        - Neither set
            gets all updates at once, no added waits
            the feed timestamp is just equal to the maximum timestamp
        - Only `polling_rate`
            gets updates within time slice (previous time + `polling_rate` seconds)
            the feed timestamp is right side of slice
        - Only `playback_speed`
            gets single update, enforcing a wait to the adjusted timestamp
            the feed timestamp is just equal to the update timestamp
        - Both set
            gets updates within timeslice and adds appropriate wait
            the feed timestamp is right side of slice
        """
        df_slice = (
            # group within next time slice if using polling_rate
            self.df[self.vehicle_positions_last_updated : self.next_poll_time]
            if self.polling_rate
            else (
                # next individual update if using playback_speed
                self.df.iloc[[self._vehicle_positions_count]]
                if self.playback_speed
                # every update at once, if using neither
                else self.df
            )
        )
        # wait as required by playback_speed
        if self.playback_speed:
            pause.until(self.next_poll_time)

        self._vehicle_positions = zip(
            df_slice["vehicle_id"].to_list(),
            df_slice[self.fields].to_dict("records"),
        )
        self._vehicle_positions_count += 1

    @property
    def vehicle_positions(self):
        return self._vehicle_positions

    # all updates are sparse
    vehicle_positions_sparse = vehicle_positions


def main(**kwargs):
    parser = ArgumentParser(
        description="Publish recorded data to redis/elasticache",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--source",
        type=str,
        help="filename or endpoint url",
    )
    parser.add_argument(
        "--polling-rate",
        type=float,
        help="timeslice for grouping updates, default=None",
    )
    parser.add_argument(
        "--playback-speed",
        type=float,
        help="timestamp vs actual time, default=None",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        help="datetime-like string (ex. '2021-08-22T00:03:01.2'), default=None",
    )
    parser.add_argument(
        "--end-time",
        type=str,
        help="datetime-like string (ex. '2021-08-22T00:08:01.2'), default=None",
    )
    parser.add_argument(
        "--repeat",
        action="store_true",
        help="whether to keep continually loop over the same data, default=False",
    )
    parser.add_argument(
        "--use-original-time",
        action="store_true",
        help="do not update timestamp based on current time",
    )
    parser.add_argument(
        "--begin-with-current-time",
        action="store_true",
        help="filter dataset to begin at the current time",
    )
    parser.add_argument("--timezone", type=str, help="original timezone")
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=str, help="port for redis endpoint")
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
    parser.add_argument(
        "--get-statistics",
        action="store_true",
        help="prints various statistics about the timing and underlying data",
    )
    parser.add_argument("--api-url", type=str)
    args, _ = parser.parse_known_args(namespace=Namespace(**kwargs))

    # get from command line args or environment variables
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    source = args.source or os.environ.get("SOURCE")
    polling_rate = args.polling_rate or float(os.environ.get("POLLING_RATE", 0)) or None
    playback_speed = (
        args.playback_speed or float(os.environ.get("PLAYBACK_SPEED", 0)) or None
    )
    start_time = args.start_time or os.environ.get("START_TIME")
    end_time = args.end_time or os.environ.get("END_TIME")
    should_repeat = args.repeat or ("REPEAT" in os.environ)
    redis_url = args.redis_url or os.environ.get("REDIS_URL") or "localhost"
    redis_port = args.redis_port or os.environ.get("REDIS_PORT") or 6379
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

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    recorded_data_playback = RecordedDataPlayback(
        source=source,
        polling_rate=polling_rate,
        playback_speed=playback_speed,
        start_time=start_time,
        end_time=end_time,
        should_repeat=should_repeat,
        time_correction=not args.use_original_time,
        begin_with_current_time=args.begin_with_current_time,
        timezone=args.timezone,
        vehicle_list=vehicle_list,
    )

    send_to_api = args.api_url is not None and not args.api_url == ""

    if send_to_api:
        logging.info("Using API")
    else:
        logging.info("Using service")

    if not send_to_api:
        aws_cfg = Config(
            local_development=True,
            redis_url=redis_url,
            redis_port=redis_port,
        )
        logging.info(f"{aws_cfg=}")
        aws_publisher = AWSPublisher(aws_cfg, agency_name, vehicle_list, trip_list)

    # keep track of runtime (mainly useful for debugging polling_rate/playback_speed)
    if args.get_statistics:
        loop_start_time = datetime.now()
        loop_count = 0

    try:
        while True:
            # update vehicle_positions
            recorded_data_playback.poll_vehicle_positions()
            # update all vehicles
            for vehicle_id, fields in recorded_data_playback.vehicle_positions:
                print(vehicle_id)
                if send_to_api:
                    if vehicle_list is None or vehicle_id not in vehicle_list:
                        continue

                    print(vehicle_id)

                    vehicle = fields

                    body = {
                        "id": vehicle["vehicle_id"],
                        "is_deleted": False,
                        "vehicle": {
                            "trip": {
                                "trip_id": vehicle["trip_id"],
                                "route_id": vehicle["trip_id"],
                                "direction_id": 0,
                                "start_time": str(vehicle["timestamp"]),
                                "start_date": str(vehicle["timestamp"]),
                                "schedule_relationship": "SCHEDULED",
                            },
                            "vehicle": {
                                "id": vehicle["vehicle_id"],
                                "label": vehicle["vehicle_id"],
                                "license_plate": vehicle["vehicle_id"],
                            },
                            "position": {
                                "latitude": vehicle["latitude"],
                                "longitude": vehicle["longitude"],
                                "bearing": vehicle["bearing"],
                                "odometer": 0,
                                "speed": vehicle["speed"],
                            },
                            "current_stop_sequence": 0,
                            "stop_id": None,
                            "current_status": "INCOMING_AT",
                            "timestamp": int(vehicle["timestamp"]),
                            "congestion_level": "UNKNOWN_CONGESTION_LEVEL",
                            "occupancy_status": "EMPTY",
                        },
                    }

                    print(requests.post(args.api_url, json.dumps(body)).content)
                else:
                    aws_publisher.update_vehicle_position(vehicle_id, fields)

            if not send_to_api:
                aws_publisher.set_last_updated(
                    recorded_data_playback.vehicle_positions_last_updated.timestamp()
                )

            if args.get_statistics:
                loop_count += 1

            if recorded_data_playback.is_done:
                logging.info("finished publishing, exiting")
                break

            try:
                args.callback()
            except Exception as e:
                print(e)
    # still exit normally on keyboard interrupt
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
        pass

    if args.get_statistics:
        total_seconds = (datetime.now() - loop_start_time).total_seconds()
        logging.info(f"completed {loop_count} loops in {total_seconds:.1f} seconds")
        recorded_data_playback.get_statistics(vehicle_list=vehicle_list)


if __name__ == "__main__":
    main()
