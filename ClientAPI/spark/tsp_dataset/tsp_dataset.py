import json
from argparse import Namespace, ArgumentParser, ArgumentTypeError
from datetime import date, datetime, timedelta
from typing import List, Optional, Set, Tuple

from pyspark.sql import SparkSession, DataFrame, Window
from pyspark.sql.functions import (
    element_at,
    col,
    concat,
    lit,
    expr,
    to_date,
    when,
    sum,
    from_utc_timestamp,
    desc,
    coalesce,
    lag,
    row_number,
    udf,
    rank,
    acos,
    cos,
    sin,
    mean,
    stddev,
    toRadians,
)
from pyspark.sql.types import LongType, TimestampType, IntegerType
import xml.etree.ElementTree as ET

MODE_PROD = "prod"
MODE_LOCAL = "local"


def haversine(lat_p1, lon_p1, lat_p2, lon_p2):
    # Returns the Great Circle Distance in m
    return (
        acos(
            sin(toRadians(lat_p1)) * sin(toRadians(lat_p2))
            + cos(toRadians(lat_p1))
            * cos(toRadians(lat_p2))
            * cos(toRadians(lon_p1) - toRadians(lon_p2))
        )
        * lit(6371.0)
        * lit(1000)
    )


def valid_date(s: str) -> date:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise ArgumentTypeError(msg)


def valid_date_range(s: str) -> Optional[Tuple[date, date]]:
    try:
        date_range = json.loads(s)
        assert isinstance(date_range, list) and len(date_range) == 2
        date_range = [
            datetime.strptime(date_, "%Y-%m-%d").date() for date_ in date_range
        ]
        assert date_range[0] <= date_range[1]
        return tuple(date_range)
    except (AssertionError, ValueError):
        print(ArgumentTypeError(f"Not a valid date range: {s!r}."))


def generate_dates(
    today: date,
    date_range: Optional[Tuple[date, date]],
    pattern: List[int],
    add_previous_day: bool = False,
) -> Set[date]:
    if date_range:
        date_start, date_end = date_range
        return {
            date_start + timedelta(days=d)
            for d in range((date_end - date_start).days + 1)
        }

    dates = {today - timedelta(days=d) for d in pattern}

    if add_previous_day:
        prev_dates = {d - timedelta(days=1) for d in dates}
        dates = dates.union(prev_dates)

    return dates


def generate_all_dates(dates: Set[date]) -> Set[date]:
    if len(dates) == 0:
        return {}

    date_start, date_end = min(dates) - timedelta(days=1), max(dates) + timedelta(
        days=1
    )
    return {
        date_start + timedelta(days=d) for d in range((date_end - date_start).days + 1)
    }


class TspDatasetJob:
    def __init__(self, opts: Namespace):
        self.opts = opts
        self.spark = self._init_spark_context()
        self.spark.sparkContext.setLogLevel("info")
        log4j = self.spark.sparkContext._jvm.org.apache.log4j
        self.logger = log4j.LogManager.getLogger("TspDatasetJob")

        self.vehicle_log_columns = ["gtt_opticom_log_id"] + [
            f"vehicle_logs.{c}"
            for c in [
                "gtt_vehicle_log_id",
                "gtt_trip_id",
                "event_id",
                "event_type",
                "SerialNumber",
                "RSSI",
                "VehicleMode",
                "VehicleGPSCStat",
                "VehicleGPSCSatellites",
                "OpStatus",
                "TurnStatus",
                "VehicleClass",
                "ConditionalPriority",
                "VehicleDiagnosticValue",
                "lat",
                "lon",
                "speed",
                "heading",
                "timestamp",
                "date",
            ]
        ]

        self.vehicle_events_columns = [
            "event_id",
            "event_type",
            "stop_event_id",
            "trip_data.date",
        ]
        self.stop_event_columns = [
            "stop_event_id",
            "stopName",
            "stopIndex",
            "dwellTime",
            "trackTime",
            "trip_data.date",
        ]
        self.supported_event_types = ["stop arrive", "stop depart"]

    def _init_spark_context(self):
        spark = SparkSession.builder.appName("TSP dataset job").config(
            "spark.sql.sources.partitionOverwriteMode", "dynamic"
        )

        if self.opts.mode == MODE_LOCAL:
            spark = (
                spark.master("local[*]")
                .config("spark.executor.memory", "7g")
                .config("spark.driver.memory", "7g")
                .config("spark.memory.offHeap.enabled", "true")
                .config("spark.memory.offHeap.size", "7g")
            )

        return spark.getOrCreate()

    def _read_trip_data(
        self, add_previous_day: bool = True, filter_result: bool = True
    ) -> DataFrame:
        dates = generate_dates(
            self.opts.date,
            self.opts.date_range,
            self.opts.pattern,
            add_previous_day=add_previous_day,
        )
        allDates = generate_all_dates(dates)

        input_files = [
            f"{self.opts.input_bucket_trip_data}{date}/" for date in allDates
        ]
        self.logger.info(f"Read trip data: {input_files}")

        null = lit(None).cast(IntegerType())

        trip_data = (
            self.spark.read.options(
                basePath=self.opts.input_bucket_trip_data.rsplit("/", 1)[0]
            )
            .parquet(
                self.opts.input_bucket_trip_data
                + "{"
                + ",".join(map(str, allDates))
                + "}"
            )
            .withColumn("gtt_vehicle_log_id", expr("uuid()"))
            .withColumn(
                "gtt_trip_id",
                concat(
                    col("deviceID"), lit("_"), col("logID"), lit("_"), col("routeName")
                ),
            )
            .withColumn("gtt_opticom_log_id", expr("uuid()"))
            .withColumn("SerialNumber", null)
            .withColumn("RSSI", null)
            .withColumn("lon", element_at(col("loc.coordinates"), 1))
            .withColumn("lat", element_at(col("loc.coordinates"), 2))
            .withColumnRenamed("mph", "speed")
            .withColumnRenamed("dir", "heading")
            .withColumn("VehicleMode", null)
            .withColumn("VehicleGPSCStat", null)
            .withColumn("VehicleGPSCSatellites", null)
            .withColumn("OpStatus", null)
            .withColumn("TurnStatus", null)
            .withColumn("VehicleClass", null)
            .withColumn("ConditionalPriority", null)
            .withColumn("VehicleDiagnosticValue", null)
            .withColumn(
                "time", from_utc_timestamp(col("time"), self.opts.local_timezone)
            )
            .withColumnRenamed("time", "timestamp")
            .withColumnRenamed("event", "event_type")
            .withColumn(
                "event_id",
                when(
                    col("event_type").isin(self.supported_event_types), expr("uuid()")
                ),
            )
            .withColumn("date", to_date(col("timestamp")))
            .filter(col("date").isin(dates))
            .drop("__v", "_id")
            .alias("trip_data")
        )

        if filter_result:
            filter_for_dates = generate_dates(
                self.opts.date, self.opts.date_range, self.opts.pattern
            )
            self.logger.info(
                f"Filter trip data: {[f'{d:%Y-%m-%d}' for d in filter_for_dates]}"
            )

            trip_data = trip_data.filter(col("date").isin(filter_for_dates))
        # If the tracktime is beyond 3 standard deviation (covers 99.7% values) we are considering it to be an outliner and it will be filtered out.
        mean_std = trip_data.agg(
            *[
                mean(colName).alias("{}{}".format("mean_", colName))
                for colName in ["tracktime"]
            ],
            *[
                stddev(colName).alias("{}{}".format("stddev_", colName))
                for colName in ["tracktime"]
            ],
        )
        mean_std.show()
        # removing the outliners with more than 3 standard deviation as it would cover 99.97% values and remove only the outliners
        trip_data = trip_data.filter(
            (
                (
                    col("tracktime")
                    < (
                        mean_std.first()["mean_tracktime"]
                        + (3 * mean_std.first()["stddev_tracktime"])
                    )
                )
                & (
                    col("tracktime")
                    > (
                        mean_std.first()["mean_tracktime"]
                        - (3 * mean_std.first()["stddev_tracktime"])
                    )
                )
            )
            | col("tracktime").isNull()
            | (col("tracktime") == "")
        )
        # filtering data if the speed (mph), lat and long are not within the specified limits which might be an incorrect data from CVP.
        trip_data = trip_data.filter(
            (element_at(col("loc.coordinates"), 1) < 180)
            & (element_at(col("loc.coordinates"), 1) > -180)
            & (element_at(col("loc.coordinates"), 2) < 90)
            & (element_at(col("loc.coordinates"), 2) > -90)
        )
        # Removing rows with speed outliners
        trip_data = trip_data.filter((col("speed") >= 0) & (col("speed") < 100))
        return trip_data

    def _read_trip_log(
        self, add_previous_day: bool = True, filter_result: bool = True
    ) -> DataFrame:
        dates = generate_dates(
            self.opts.date,
            self.opts.date_range,
            self.opts.pattern,
            add_previous_day=add_previous_day,
        )
        allDates = generate_all_dates(dates)

        input_files = [f"{self.opts.input_bucket_trip_log}{date}/" for date in allDates]
        self.logger.info(f"Read trip logs: {input_files}")

        trip_log = (
            self.spark.read.options(
                basePath=self.opts.input_bucket_trip_log.rsplit("/", 1)[0]
            )
            .parquet(
                self.opts.input_bucket_trip_log
                + "{"
                + ",".join(map(str, allDates))
                + "}"
            )
            .withColumn(
                "gtt_trip_id",
                concat(
                    col("deviceID"), lit("_"), col("logID"), lit("_"), col("routeName")
                ),
            )
            .withColumn(
                "startTime", from_utc_timestamp("startTime", self.opts.local_timezone)
            )
            .withColumn(
                "endTime", from_utc_timestamp("endTime", self.opts.local_timezone)
            )
            .withColumn(
                "uploadDate", from_utc_timestamp("uploadDate", self.opts.local_timezone)
            )
            .withColumn("date", to_date(col("startTime")))
            .filter(col("date").isin(dates))
            .drop("__v", "_id", "tzOffset", "utc_offset")
            .alias("trip_log")
        )

        if filter_result:
            filter_for_dates = generate_dates(
                self.opts.date, self.opts.date_range, self.opts.pattern
            )
            self.logger.info(
                f"Filter trip logs: {[f'{d:%Y-%m-%d}' for d in filter_for_dates]}"
            )

            trip_log = trip_log.filter(col("date").isin(filter_for_dates))

        return trip_log

    def _read_opticom_log(
        self,
        lookback_window: int = None,
        add_previous_day: bool = True,
        filter_result: bool = True,
    ) -> DataFrame:
        read_for_dates = generate_dates(
            self.opts.date,
            self.opts.date_range,
            self.opts.pattern,
            add_previous_day=add_previous_day,
        )
        input_files = [
            f"{self.opts.input_bucket_opticom_log}{date}" for date in read_for_dates
        ]
        self.logger.info(f"Read opticom logs: {input_files}")

        device_log = (
            self.spark.read.options(
                basePath=self.opts.input_bucket_opticom_log.rsplit("/", 1)[0]
            )
            .parquet(
                self.opts.input_bucket_opticom_log
                + "{"
                + ",".join(map(str, read_for_dates))
                + "}"
            )
            .withColumn(
                "event_start",
                (col("EndDateTime").cast(LongType()) - col("Duration")).cast(
                    TimestampType()
                ),
            )
            .withColumn("date", to_date(col("StartDateTime")))
            .alias("opticom_log")
        )

        if filter_result:
            filter_for_dates = generate_dates(
                self.opts.date, self.opts.date_range, self.opts.pattern
            )
            self.logger.info(
                f"Filter opticom logs: {[f'{d:%Y-%m-%d}' for d in filter_for_dates]}"
            )

            device_log = device_log.filter(col("date").isin(filter_for_dates))

        return device_log

    def _read_device_config(
        self,
        lookback_window: int = None,
        add_previous_day: bool = True,
        filter_result: bool = True,
    ) -> DataFrame:
        read_for_dates = generate_dates(
            self.opts.date,
            self.opts.date_range,
            self.opts.pattern,
            add_previous_day=add_previous_day,
        )
        input_files = [
            f"{self.opts.input_bucket_device_config}{date}" for date in read_for_dates
        ]
        self.logger.info(f"Read device configuration: {input_files}")

        def findLatitude(xml):
            try:
                val = int(
                    ET.fromstring(xml)
                    .find("DeviceIdentity")
                    .find("DeviceLocation")
                    .find("LatitudeRaw")
                    .text
                )
                if val < 0:
                    val = val * (-1)
                    coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
                    coord = coord * (-1)
                else:
                    coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
                return coord
            except:
                return 0.0

        def findLongitude(xml):
            try:
                val = int(
                    ET.fromstring(xml)
                    .find("DeviceIdentity")
                    .find("DeviceLocation")
                    .find("LongitudeRaw")
                    .text
                )
                if val < 0:
                    val = val * (-1)
                    coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
                    coord = coord * (-1)
                else:
                    coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
                return coord
            except:
                return 0.0

        lat_udf = udf(findLatitude)
        lon_udf = udf(findLongitude)

        device_config = (
            self.spark.read.options(
                basePath=self.opts.input_bucket_device_config.rsplit("/", 1)[0]
            )
            .parquet(
                self.opts.input_bucket_device_config
                + "{"
                + ",".join(map(str, read_for_dates))
                + "}"
            )
            .withColumn("date", col("date_ran"))
            .withColumn("Lat", lat_udf("DeviceConfigurationXml"))
            .withColumn("Lon", lon_udf("DeviceConfigurationXml"))
            .alias("device_config")
        )

        if filter_result:
            filter_for_dates = generate_dates(
                self.opts.date, self.opts.date_range, self.opts.pattern
            )
            self.logger.info(
                f"Filter device configuration: {[f'{d:%Y-%m-%d}' for d in filter_for_dates]}"
            )

            device_config = device_config.filter(col("date").isin(filter_for_dates))

        return device_config

    def _read_intersection_status_report(
        self,
        lookback_window: int = None,
        add_previous_day: bool = True,
        filter_result: bool = True,
    ) -> DataFrame:
        read_for_dates = generate_dates(
            self.opts.date,
            self.opts.date_range,
            self.opts.pattern,
            add_previous_day=add_previous_day,
        )
        input_files = [
            f"{self.opts.input_bucket_intersection_status_report}{date}"
            for date in read_for_dates
        ]
        self.logger.info(f"Read intersection status report: {input_files}")

        intersection_status_report = (
            self.spark.read.options(
                basePath=self.opts.input_bucket_intersection_status_report.rsplit(
                    "/", 1
                )[0]
            )
            .parquet(
                self.opts.input_bucket_intersection_status_report
                + "{"
                + ",".join(map(str, read_for_dates))
                + "}"
            )
            .withColumn("date", col("date_ran"))
            .alias("intersection_status_report")
        )

        if filter_result:
            filter_for_dates = generate_dates(
                self.opts.date, self.opts.date_range, self.opts.pattern
            )
            self.logger.info(
                f"Filter intersection status report: {[f'{d:%Y-%m-%d}' for d in filter_for_dates]}"
            )

            intersection_status_report = intersection_status_report.filter(
                col("date").isin(filter_for_dates)
            )

        return intersection_status_report

    def _deduplicate_opticom_log(self, opticom_log: DataFrame) -> DataFrame:
        """
        https://gttwiki.atlassian.net/wiki/spaces/GD/pages/2523824129/Connecting+CVP+data+to+meaningful+Opticom+Logs
        Trying to deduplicate opticom logs before joining with other datasets
        When grouped by 'LocationName', 'Channel', 'VehicleName'
        Take only last event by StartDateTime within 15 minutes window (15 * 60 = 900 seconds)
        time lag(x), diff, cumul(diff),  session_id, rn
        --------------------------------------------------
        1,   null,   0,    0,            0           4
        5,   1,      4,    4,            0           3
        10,  5,      5,    9,            0           2
        15,  10,     5,    14,           0           (1)
        18,  15,     3,    17,           1           (1)
        40,  18,     22,   39,           2           2
        42,  40,     2,    41,           2           (1)
        """
        window_spec = Window.partitionBy(
            "LocationName", "Channel", "VehicleName"
        ).orderBy("StartDateTime")
        session_window_spec = Window.partitionBy(
            "LocationName", "Channel", "VehicleName", "session_id"
        ).orderBy(desc("StartDateTime"))

        return (
            opticom_log.withColumn(
                "prev_time",
                coalesce(lag("StartDateTime").over(window_spec), col("StartDateTime")),
            )
            .withColumn(
                "diff",
                col("StartDateTime").cast(LongType())
                - col("prev_time").cast(LongType()),
            )
            .withColumn("cumul_diff", sum("diff").over(window_spec))
            .withColumn(
                "session_id", (col("cumul_diff") / (15 * 60)).cast(IntegerType())
            )
            .withColumn("rn", row_number().over(session_window_spec))
            .filter(col("rn") == 1)
            .drop("rn", "session_id", "cumul_diff", "diff", "prev_time")
        )

    def run(self) -> None:
        intersection_status_report = self._read_intersection_status_report(
            add_previous_day=False, filter_result=False
        ).repartition(col("date"))
        device_config = self._read_device_config(
            add_previous_day=False, filter_result=False
        ).repartition(col("date"))
        trip_data = self._read_trip_data().repartition(col("date"))
        trip_log = self._read_trip_log().repartition(col("date"))
        opticom_log = self._read_opticom_log(
            add_previous_day=False, filter_result=False
        ).repartition(col("date"))
        opticom_log_columns = ["opticom_log_with_id.gtt_opticom_log_id"] + [
            f"opticom_log_with_id.{x}" for x in opticom_log.schema.names
        ]

        if self.opts.mode == MODE_PROD:
            opticom_log = opticom_log.cache()
            trip_data = trip_data.cache()
            trip_log = trip_log.cache()
            device_config = device_config.cache()

        trip_data_device_log = (
            trip_data.join(trip_log.hint("broadcast"), on="gtt_trip_id")
            .join(
                self._deduplicate_opticom_log(opticom_log),
                [
                    col("trip_log.vehicleName") == col("opticom_log.VehicleName"),
                    # corresponding record in opticom_log should appear within 10 seconds
                    (
                        col("opticom_log.EndDateTime").cast(LongType())
                        - col("trip_data.timestamp").cast(LongType())
                    )
                    >= 0,
                    (
                        col("opticom_log.EndDateTime").cast(LongType())
                        - col("trip_data.timestamp").cast(LongType())
                    )
                    <= 10,
                ],
            )
            .withColumn(
                "rn",
                row_number().over(
                    Window.partitionBy("OpticomDeviceLogId").orderBy(desc("timestamp"))
                ),
            )
            .filter(col("rn") == 1)
            .dropDuplicates(["gtt_vehicle_log_id"])
            .select("gtt_vehicle_log_id", "OpticomDeviceLogId", "gtt_opticom_log_id")
            .alias("trip_data_device_log")
        )

        if self.opts.mode == MODE_PROD:
            trip_data_device_log = trip_data_device_log.cache()

        vehicle_logs = (
            trip_data.alias("vehicle_logs")
            .join(trip_data_device_log, on="gtt_vehicle_log_id", how="left")
            .withColumn(
                "new_opticom_log_id",
                when(
                    col("trip_data_device_log.OpticomDeviceLogId").isNotNull(),
                    col("trip_data_device_log.gtt_opticom_log_id"),
                ),
            )
            .drop("gtt_opticom_log_id", "OpticomDeviceLogId")
            .withColumnRenamed("new_opticom_log_id", "gtt_opticom_log_id")
        )

        opticom_log_with_id = opticom_log.join(
            trip_data_device_log, on="OpticomDeviceLogId", how="left"
        ).alias("opticom_log_with_id")

        stop_events = trip_data.filter(
            col("event_type").isin(["stop arrive", "stop depart"])
        ).withColumn("stop_event_id", expr("uuid()"))

        # Calculate the Geofence using the OpticomDevice
        intersection_logs_and_locations_window = Window.partitionBy(
            "gtt_opticom_log_id"
        ).orderBy(desc("device_config_parsed.date"))
        intersection_logs_and_locations = (
            device_config.select(["deviceid", "lat", "lon", "date"])
            .filter(
                (col("lat") < 90)
                & (col("lat") > -90)
                & (col("lon") < 180)
                & (col("lon") > -180)
            )
            .alias("device_config_parsed")
            .join(
                opticom_log_with_id.filter(col("gtt_opticom_log_id").isNotNull()),
                on="deviceid",
                how="inner",
            )
            .withColumn("rank", rank().over(intersection_logs_and_locations_window))
            .filter(col("rank") == 1)
            .drop("rank")
            .dropDuplicates(subset=["gtt_opticom_log_id", "date"])
            .select(
                [
                    "gtt_opticom_log_id",
                    "device_config_parsed.deviceid",
                    "device_config_parsed.lat",
                    "device_config_parsed.lon",
                ]
            )
            .alias("opticom_log_with_location")
        )

        vehicle_logs_window = Window.partitionBy("gtt_trip_id").orderBy(
            "vehicle_logs.timestamp"
        )
        intersectionvehiclelocations = (
            vehicle_logs.filter(
                (col("lat") < 90)
                & (col("lat") > -90)
                & (col("lon") < 180)
                & (col("lon") > -180)
            )
            .join(intersection_logs_and_locations, on="gtt_opticom_log_id", how="left")
            .select(
                [
                    "gtt_trip_id",
                    "gtt_vehicle_log_id",
                    "gtt_opticom_log_id",
                    col("vehicle_logs.lat").alias("vehicle_lat"),
                    col("vehicle_logs.lon").alias("vehicle_lon"),
                    "vehicle_logs.timestamp",
                    col("opticom_log_with_location.lat").alias("intersection_lat"),
                    col("opticom_log_with_location.lon").alias("intersection_lon"),
                ]
            )
            .withColumn("rn", row_number().over(vehicle_logs_window))
            .cache()
            .alias("vehicle_logs_intersection_location")
        )

        intersectionvehiclelocations_filtered = (
            intersectionvehiclelocations.filter(col("gtt_opticom_log_id").isNotNull())
            .withColumnRenamed("gtt_trip_id", "gtt_trip_id_right")
            .withColumnRenamed("rn", "rn_right")
            .withColumnRenamed("intersection_lat", "intersection_lat_right")
            .withColumnRenamed("intersection_lon", "intersection_lon_right")
            .withColumnRenamed("gtt_opticom_log_id", "gtt_opticom_log_id_right")
            .withColumnRenamed("timestamp", "timestamp_right")
            .select(
                [
                    "gtt_trip_id_right",
                    "rn_right",
                    "intersection_lat_right",
                    "intersection_lon_right",
                    "gtt_opticom_log_id_right",
                    "timestamp_right",
                ]
            )
            .alias("vehicle_logs_intersection_location_filtered")
        )

        true_gtt_opticom_id_conditions = [
            col("vehicle_logs_intersection_location.gtt_trip_id")
            == col("vehicle_logs_intersection_location_filtered.gtt_trip_id_right"),
            col("vehicle_logs_intersection_location.rn")
            - col("vehicle_logs_intersection_location_filtered.rn_right")
            <= 0,
            col("vehicle_logs_intersection_location.rn")
            - col("vehicle_logs_intersection_location_filtered.rn_right")
            > -300,
            haversine(
                col("vehicle_logs_intersection_location.vehicle_lat"),
                col("vehicle_logs_intersection_location.vehicle_lon"),
                col(
                    "vehicle_logs_intersection_location_filtered.intersection_lat_right"
                ),
                col(
                    "vehicle_logs_intersection_location_filtered.intersection_lon_right"
                ),
            )
            < 50,
        ]
        true_gtt_opticom_id_window = Window.partitionBy(
            "vehicle_logs_intersection_location.gtt_vehicle_log_id"
        ).orderBy(desc("diff"))
        true_gtt_opticom_id = (
            intersectionvehiclelocations.join(
                intersectionvehiclelocations_filtered,
                on=true_gtt_opticom_id_conditions,
                how="inner",
            )
            .drop("vehicle_logs_intersection_location.gtt_opticom_log_id")
            .withColumn(
                "diff",
                col("vehicle_logs_intersection_location.rn")
                - col("vehicle_logs_intersection_location_filtered.rn_right"),
            )
            .withColumn("rank", rank().over(true_gtt_opticom_id_window))
            .filter(col("rank") == 1)
            .drop("rank")
            .select(
                [
                    "vehicle_logs_intersection_location.gtt_vehicle_log_id",
                    col(
                        "vehicle_logs_intersection_location_filtered.gtt_opticom_log_id_right"
                    ).alias("gtt_opticom_log_id"),
                ]
            )
        )

        vehicle_logs = (
            vehicle_logs.drop("gtt_opticom_log_id")
            .join(true_gtt_opticom_id, on="gtt_vehicle_log_id", how="left")
            .alias("vehicle_logs")
        )

        if self.opts.mode == MODE_PROD:
            stop_events = stop_events.cache()

        mode = "overwrite"
        vehicle_logs.select(self.vehicle_log_columns).repartition(10).write.partitionBy(
            "date"
        ).parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/vehicle_logs/agency={self.opts.agency}",
            mode=mode,
        )

        opticom_log_with_id.select(opticom_log_columns).repartition(
            1
        ).write.partitionBy("date").parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/opticom_device_log/agency={self.opts.agency}",
            mode=mode,
        )

        stop_events.select(self.vehicle_events_columns).repartition(
            1
        ).write.partitionBy("date").parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/vehicle_events/agency={self.opts.agency}",
            mode=mode,
        )

        stop_events.select(self.stop_event_columns).repartition(1).write.partitionBy(
            "date"
        ).parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/stop_events/agency={self.opts.agency}",
            mode=mode,
        )

        trip_log.repartition(1).write.partitionBy("date").parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/trips/agency={self.opts.agency}",
            mode=mode,
        )

        device_config.repartition(1).write.partitionBy("date").parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/device_configuration/agency={self.opts.agency}",
            mode=mode,
        )

        intersection_status_report.repartition(1).write.partitionBy("date").parquet(
            path=f"{self.opts.output_bucket}/tsp_source_data/tsp_dataset/intersection_status_report/agency={self.opts.agency}",
            mode=mode,
        )


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--input-bucket-trip-data",
        required=True,
        default="s3a://backup-gtt-etl-data-dev/sfmta-etl-data/CVP/TRIPDATAS/PARTITION/date_ran=",
    )
    parser.add_argument(
        "--input-bucket-trip-log",
        required=True,
        default="s3a://backup-gtt-etl-data-dev/sfmta-etl-data/CVP/TRIPLOGS/PARTITION/date_ran=",
    )
    parser.add_argument(
        "--input-bucket-opticom-log",
        required=True,
        default="s3a://backup-gtt-etl-data-dev/sfmta-etl-data/CMS/OPTICOMDEVICELOG/PARTITION/starttime=",
    )
    parser.add_argument(
        "--input-bucket-device-config",
        required=True,
        default="s3a://backup-gtt-etl-data-dev/sfmta-etl-data/CMS/DEVICECONFIGURATION/PARTITION/date_ran=",
    )
    parser.add_argument(
        "--input-bucket-intersection-status-report",
        required=True,
        default="s3a://backup-gtt-etl-data-dev/sfmta-etl-data/CMS/INTERSECTIONSTATUSREPORT/PARTITION/date_ran=",
    )
    parser.add_argument("--output-bucket", required=False, default="s3a://gtt-etl-dev")
    parser.add_argument("--agency", required=False, default="sfmta")
    parser.add_argument("--local-timezone", required=False, default="PST")
    parser.add_argument("--date", required=False, type=valid_date, default=date.today())
    parser.add_argument("--date-range", required=False, type=valid_date_range)
    parser.add_argument(
        "--mode", required=False, choices=(MODE_PROD, MODE_LOCAL), default=MODE_PROD
    )
    parser.add_argument("--pattern", required=True, type=int, nargs="+")
    return parser.parse_args()


if __name__ == "__main__":
    opts = parse_args()
    job = TspDatasetJob(opts)
    job.run()
