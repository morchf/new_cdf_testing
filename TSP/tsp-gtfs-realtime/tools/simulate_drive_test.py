import logging
import os
import struct
import time
from argparse import ArgumentParser
from ast import literal_eval
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd
import requests


# ToDo: import from gtt.data_model.rt_radio_message
@dataclass
class RTRadioMessage:
    unit_id: int
    vehicle_rssi: int
    latitude: float
    longitude: float
    speed: float
    heading: float
    gpsc_stat: int
    satellite_gps: int
    vehicle_id: int
    vehicle_city_id: int
    left_turn_signal: bool
    right_turn_signal: bool
    op_status: str
    vehicle_mode: str
    vehicle_class: int
    conditional_priority: int
    veh_diag_value: int


def parse_rt_radio_message(raw_bytes):
    format_string = (
        "<"
        "i"  # unit_id                UL24 + BYTE ???
        "H"  # vehicle_rssi           ??
        "2x"
        "i"  # gps_lat_dddmmmmmm      SLONG
        "i"  # gps_lon_dddmmmmmm      SLONG
        "c"  # velocity_mpsd5         UBYTE
        "c"  # hdg_deg2               UBYTE
        "H"  # gpsc_stat              UWORD
        "I"  # satellite_gps          ULONG
        "H"  # vehicle_id             UWORD?
        "B"  # vehicle_city_id        UBYTE?
        "B"  # veh_mode_op_turn       UBYTE
        "B"  # vehicle_class          UBYTE
        "B"  # conditional_priority   UBYTE
        "2x"
        "i"  # veh_diag_value         UBYTE?
    )
    (
        unit_id,
        vehicle_rssi,
        gps_lat_dddmmmmmm,
        gps_lon_dddmmmmmm,
        velocity_mpsd5,
        hdg_deg2,
        gpsc_stat,
        satellite_gps,
        vehicle_id,
        vehicle_city_id,
        veh_mode_op_turn,
        vehicle_class,
        conditional_priority,
        veh_diag_value,
    ) = struct.unpack(format_string, raw_bytes)
    # convert back to decimal degrees
    latitude = (-1 if gps_lat_dddmmmmmm < 0 else 1) * (
        abs(gps_lat_dddmmmmmm) // 1000000 + abs(gps_lat_dddmmmmmm) % 1000000 / 600000
    )
    longitude = (-1 if gps_lon_dddmmmmmm < 0 else 1) * (
        abs(gps_lon_dddmmmmmm) // 1000000 + abs(gps_lon_dddmmmmmm) % 1000000 / 600000
    )
    # convert back to m/s
    speed = int.from_bytes(velocity_mpsd5, byteorder="little") / 5
    # convert back to deg
    heading = 2 * int.from_bytes(hdg_deg2, byteorder="little") - 1
    # split mode_op_turn
    left_turn_signal = bool(veh_mode_op_turn & 0x01)  # first bit
    right_turn_signal = bool(veh_mode_op_turn & 0x02)  # second bit
    op_status = bin(veh_mode_op_turn & 0x1C)  # 3-5th bit
    vehicle_mode = bin(veh_mode_op_turn & 0xE0)  # 6-8th bit
    return RTRadioMessage(
        unit_id,
        vehicle_rssi,
        latitude,
        longitude,
        speed,
        heading,
        gpsc_stat,
        satellite_gps,
        vehicle_id,
        vehicle_city_id,
        left_turn_signal,
        right_turn_signal,
        op_status,
        vehicle_mode,
        vehicle_class,
        conditional_priority,
        veh_diag_value,
    )


def dataframe_from_txt(
    filename: Union[str, Path],
    start_time: pd.Timestamp = None,
    end_time: pd.Timestamp = None,
):
    """preprocess RTRadioMessages.txt file to return sorted dataframe

    data is currently expected to be in the following csv format with `;` separator
        13:28:00;GTT/GTT/VEH/EVP/2101/2101FP0733/RTRADIO;b'W\x07\x83\x00\x00\x00\x00\x00\x1f\x18\xa8\x02\xc0\x87{\xfa\x00\x00\xc9\x832\x1d\n\x11\x01\x00\t&\x0e\x00\x00\x00\x00\x00\x00\x00'
        13:28:01;GTT/GTT/VEH/EVP/2101/2101FP0733/RTRADIO;b'W\x07\x83\x00\x00\x00\x00\x00\x1f\x18\xa8\x02\xc0\x87{\xfa\x00\x00\xc9\x832\x1d\n\x11\x01\x00\t&\x0e\x00\x00\x00\x00\x00\x00\x00'
        ...


    Args:
        filename (str): local file
        start_time (pandas.Timestamp): Optional, minimum timestamp
        end_time (pandas.Timestamp): Optional, maximum timestamp

    Raises:
        FileNotFoundError: unable to find given parquet file
        ValueError: start_time/end_time is not in the time range of the data
    """
    # make sure file exists
    file = Path(filename).expanduser()
    logging.debug(f"using file: '{file}'")
    if not file.is_file():
        raise FileNotFoundError(f"unable to find file: '{filename}'")

    # read file into dataframe
    df = pd.read_csv(
        file,
        sep=";",
        names=["timestamp", "topic", "data"],
        # parse timestamp as datetime and use as index
        index_col=["timestamp"],
        parse_dates=["timestamp"],
        # read b'...' as bytes
        converters={"data": literal_eval},
    )

    # decode data into RTRadioMessage and add fields as columns
    df = pd.concat(
        [
            df,
            pd.DataFrame([parse_rt_radio_message(d) for d in df.data], index=df.index),
        ],
        axis=1,
    )

    # correct any invalid headings to be 0
    df.loc[df.heading < 0, "heading"] = 0

    # make sure provided start_time/end_time is in the DatetimeIndex range
    if start_time and not (df.index.min() <= start_time < df.index.max()):
        raise ValueError(
            f"start_time: {start_time} not in the time range of the data: "
            f"[{df.index.min()} : {df.index.max()}]"
        )
    if end_time and not (df.index.min() <= end_time < df.index.max()):
        raise ValueError(
            f"end_time: {end_time} not in the time range of the data: "
            f"[{df.index.min()} : {df.index.max()}]"
        )

    # set start/end time to the earliest/latest update if not provided
    start_time = start_time or df.index.min()
    logging.info(f"setting start time to {start_time}")
    end_time = end_time or df.index.max()
    logging.info(f"setting end time to {end_time}")

    # ensure range does not roll over midnight since this does not work with `df.between_time`
    if end_time.date() - start_time.date():
        raise NotImplementedError(
            "Time ranges that extend beyond midnight are currently not supported"
        )

    df = df.between_time(start_time.time(), end_time.time())

    # offset times based on current time
    start_time = df.index.min()
    time_offset = pd.Timestamp.now() + pd.Timedelta(5, "sec") - start_time
    df.index += time_offset

    return df


class RecordedDataPlayback:
    """A class to drive the GTFSRealtimeTestServer using recorded data

    This should eventually be combined with the class of the same name in
    recorded_data_publisher.py to support publishing by using the GTFSRealtimeTestServer
    and subscribing with the GTFSRealtimeAPIPoller, or bypassing the poller and directly
    publishing to redis like in recorded_data_publisher.py

    The source of recorded data is a text file of RTRadioMessages on each line, but it
    could be expanded to various formats/locations

    `polling_rate` is used to periodically sample the data every `polling_rate` seconds.
    This adds latency similar to actual feed behavior. Each update can be sent
    individually without added latency by explicitly setting `polling_rate` to 0/None

    if `start_time`/`end_time` are set, recorded data is only sent if it occurs between
    these times (in the original data source time range).

    if `should_repeat` is True, playback is restarted after reaching the end

    Args:
        source (str): filename or endpoint url
        polling_rate (float): timeslice for grouping updates, default=5.0s
        start_time (float | datetime): timestamp or datetime to start, default=None
        end_time (float | datetime): timestamp or datetime to stop, default=None
        should_repeat (float | datetime): repeat once finished, default=False
    """

    # minimum data needed by VehicleSubscriber
    gps_fields = ["latitude", "longitude", "speed", "bearing"]
    fields = ["timestamp", "vehicle_id", "trip_id", *gps_fields]

    def __init__(
        self,
        source: str,
        polling_rate: float = 5.0,
        start_time: Union[datetime, float] = None,
        end_time: Union[datetime, float] = None,
        should_repeat: bool = False,
    ):
        self.source = source
        self.polling_rate = pd.Timedelta(polling_rate, "sec") if polling_rate else None

        self.start_time = pd.to_datetime(start_time)
        if start_time:
            logging.debug(f"interpreting start_time {start_time} as {self.start_time}")
        self.end_time = pd.to_datetime(end_time)
        if end_time:
            logging.debug(f"interpreting end_time {end_time} as {self.end_time}")

        self.should_repeat = should_repeat
        self._repeat_count = 0

        # self._vehicle_positions = {}
        # self._vehicle_positions_count = 0

        # pre-process file
        self.df = dataframe_from_txt(self.source, self.start_time, self.end_time)
        self.start_time, self.end_time = self.df.index.min(), self.df.index.max()
        logging.debug(f"updating times to {self.start_time=}, {self.end_time=}")

    @property
    def is_done(self):
        """checks for end of data, restarting if `should_repeat`

        if `should_repeat`, the data timestamps are reset instead of returning True

        Returns:
            bool: true if there is no more data
        """
        # data still available in current iteration
        if pd.Timestamp.now() < self.end_time:
            return False

        if not self.should_repeat:
            return True
        else:
            self._repeat_count += 1
            logging.info(f"resetting and extending playback: {self._repeat_count}")
            # self._vehicle_positions = {}
            # self._vehicle_positions_count = 0
            # offset dataframe times by total time (+ a second to track) to extend data
            time_offset = self.end_time - self.start_time + pd.Timedelta(1, "sec")
            self.df.index += time_offset
            self.start_time += time_offset
            self.end_time += time_offset
            logging.debug(f"updating times to {self.start_time=}, {self.end_time=}")
            return False

    # @property
    # def next_poll_time(self):
    #     # increment time based on vehicle/trip count. If vehicle is polled twice before
    #     # trip, this ensures the next trip update contains all data until current time
    #     # return self.last_updated + self.polling_rate
    #     return (
    #         self.last_updated + self.polling_rate
    #         if self.polling_rate
    #         else (
    #             # next update time if using playback_speed
    #             self.df.iloc[[self._vehicle_positions_count]].index[-1]
    #             if self.playback_speed
    #             # None, if using neither
    #             else None
    #         )
    #     )

    # @property
    # def vehicle_positions_last_updated(self):
    #     return (
    #         self.start_time + self._vehicle_positions_count * self.polling_rate
    #         if self.polling_rate
    #         else (
    #             # previous update time if using playback_speed
    #             self.df.iloc[[self._vehicle_positions_count - 1]].index[-1]
    #             if self.playback_speed
    #             # end_time, if using neither
    #             else self.end_time
    #         )
    #     )

    # last_updated = vehicle_positions_last_updated

    # def poll_vehicle_positions(self):
    #     """create list of tuples representing key, fields for values in time range

    #     Behavior varies based on usage of polling_rate and/or playback_speed:

    #     - Neither set
    #         gets all updates at once, no added waits
    #         the feed timestamp is just equal to the maximum timestamp
    #     - Only `polling_rate`
    #         gets updates within time slice (previous time + `polling_rate` seconds)
    #         the feed timestamp is right side of slice
    #     - Only `playback_speed`
    #         gets single update, enforcing a wait to the adjusted timestamp
    #         the feed timestamp is just equal to the update timestamp
    #     - Both set
    #         gets updates within timeslice and adds appropriate wait
    #         the feed timestamp is right side of slice
    #     """
    #     df_slice = (
    #         # group within next time slice if using polling_rate
    #         self.df[self.vehicle_positions_last_updated : self.next_poll_time]
    #         if self.polling_rate
    #         else (
    #             # next individual update if using playback_speed
    #             self.df.iloc[[self._vehicle_positions_count]]
    #             if self.playback_speed
    #             # every update at once, if using neither
    #             else self.df
    #         )
    #     )
    #     # wait as required by playback_speed
    #     if self.playback_speed:
    #         pause.until(self.next_poll_time)

    #     self._vehicle_positions = zip(
    #         df_slice["vehicle_id"].to_list(),
    #         df_slice[self.fields].to_dict("records"),
    #     )
    #     self._vehicle_positions_count += 1

    # @property
    # def vehicle_positions(self):
    #     return self._vehicle_positions

    # # all updates are sparse
    # vehicle_positions_sparse = vehicle_positions

    def get_current_gtfs_realtime(self, vehicle_id=1):
        """generates the dictionary needed for a single vehicle, could be extended

        Args:
            vehicle_id (int, optional): vehicle VID from asset_library. default=1
        """
        current_time = pd.Timestamp.now()
        current_data = (
            self.df.asof(current_time)
            if current_time > self.df.index.min()
            else self.df.iloc[0]
        )
        current_gtfs_realtime = {
            "header": {
                "gtfsRealtimeVersion": "1.0",
                "incrementality": "FULL_DATASET",
                "timestamp": int(current_time.timestamp()),
            },
            "entity": [
                {
                    "id": f"vehicle_{vehicle_id:04}",
                    "vehicle": {
                        "vehicle": {
                            "id": f"{vehicle_id:04}",
                            "label": str(vehicle_id),
                        },
                        "position": {
                            "latitude": float(current_data.latitude),
                            "longitude": float(current_data.longitude),
                            "bearing": float(current_data.heading),
                            "speed": float(current_data.speed),
                        },
                        "timestamp": int(current_data.name.timestamp()),
                    },
                },
            ],
        }
        return current_gtfs_realtime


def main():
    parser = ArgumentParser(
        description="Send recorded data to GTFS Test Server",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--gtfs-realtime-test-server-url",
        type=str,
        help="endpoint url, default=http://10.30.2.54:8080/vehiclepositions",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="filename or endpoint url, default=RTRadioMessages.txt",
    )
    parser.add_argument(
        "--polling-rate",
        type=float,
        help="timeslice for grouping updates, default=5.0s",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        help="datetime-like string (ex. '2021-08-22T00:03:01.2'), default='13:47:40'",
    )
    parser.add_argument(
        "--end-time",
        type=str,
        help="datetime-like string (ex. '2021-08-22T00:08:01.2'), default='13:59:00'",
    )
    parser.add_argument(
        "--repeat",
        action="store_true",
        help="whether to keep continually loop over the same data, default=False",
    )
    args = parser.parse_args()

    # get from command line args or environment variables
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    gtfs_realtime_test_server_url = (
        args.gtfs_realtime_test_server_url
        or os.environ.get("GTFSRealtimeTestServerUrl")
        or "http://10.30.2.54:8080/vehiclepositions"
    )
    source = args.source or os.environ.get("SOURCE") or "RTRadioMessages.txt"
    polling_rate = args.polling_rate or float(os.environ.get("POLLING_RATE", 0)) or 5.0
    start_time = args.start_time or os.environ.get("START_TIME") or "13:47:40"
    end_time = args.end_time or os.environ.get("END_TIME") or "13:59:00"
    should_repeat = args.repeat or ("REPEAT" in os.environ)

    if source != "RTRadioMessages.txt":
        raise NotImplementedError("other sources not yet implemented")

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    recorded_data_playback = RecordedDataPlayback(
        source=source,
        polling_rate=polling_rate,
        start_time=start_time,
        end_time=end_time,
        should_repeat=should_repeat,
    )

    while True:
        if recorded_data_playback.is_done:
            logging.info("finished publishing, exiting")
            break
        current_gtfs_realtime = recorded_data_playback.get_current_gtfs_realtime()
        logging.debug(current_gtfs_realtime["entity"][0])

        requests.post(gtfs_realtime_test_server_url, json=current_gtfs_realtime)
        # sleep polling_rate seconds
        time.sleep(polling_rate)


if __name__ == "__main__":
    main()
