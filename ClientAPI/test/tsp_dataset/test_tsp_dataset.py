from argparse import Namespace, ArgumentParser, ArgumentTypeError
from datetime import date, datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when

MODE_PROD = "prod"
MODE_LOCAL = "local"


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise ArgumentTypeError(msg)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--input-bucket",
        required=False,
        default="s3a://backup-gtt-etl-data/sfmta-etl-data",
    )
    parser.add_argument(
        "--output-bucket", required=False, default="s3a://gtt-etl/sfmta/tsp_source_data"
    )
    parser.add_argument("--date", required=False, type=valid_date, default=date.today())
    parser.add_argument(
        "--mode", required=False, choices=(MODE_PROD, MODE_LOCAL), default=MODE_PROD
    )
    return parser.parse_args()


def run_job(opts: Namespace) -> None:
    spark = (
        SparkSession.builder.appName("TSP dataset job")
        .master("local[*]")
        .config("spark.executor.memory", "4g")
        .config("spark.driver.memory", "4g")
        .config("spark.memory.offHeap.enabled", True)
        .config("spark.memory.offHeap.size", "4g")
        .getOrCreate()
    )

    vehicle_logs = spark.read.parquet(
        f"{opts.input_bucket}/tsp_dataset/vehicle_logs/"
    ).alias(
        "vehicle_logs"
    )  # .registerTempTable("vehicle_logs")
    trips = spark.read.parquet(f"{opts.input_bucket}/tsp_dataset/trips/").alias(
        "trips"
    )  # .registerTempTable("trips")
    vehicle_events = spark.read.parquet(
        f"{opts.input_bucket}/tsp_dataset/vehicle_events/"
    )  # .registerTempTable("vehicle_events")
    stop_events = spark.read.parquet(
        f"{opts.input_bucket}/tsp_dataset/stop_events/"
    ).alias(
        "stop_events"
    )  # .registerTempTable("stop_events")
    opticom_device_log = spark.read.parquet(
        f"{opts.input_bucket}/tsp_dataset/opticom_device_log/"
    ).alias(
        "opticom_log"
    )  # .registerTempTable("opticom_device_log")

    print(
        f'All non-gps events: {vehicle_logs.filter(col("event_id").isNotNull()).count()}'
    )
    print(f"vehicle events: {vehicle_events.count()}")
    print(f"stop events: {stop_events.count()}")
    print(f"trips: {trips.count()}")

    # All non - gps events: 186998
    # vehicle events: 176945
    # intersection events: 7618
    # stop events: 169327

    print(vehicle_logs.count())
    print(opticom_device_log.count())

    vehicle_opticom_log = vehicle_logs.join(opticom_device_log, on="gtt_opticom_log_id")
    print(vehicle_opticom_log.count())

    vehicle_logs.select(
        [
            count(when(col("gtt_opticom_log_id").isNull(), 1)).alias("nulls"),
            count(when(col("gtt_opticom_log_id").isNotNull(), 1)).alias("not nulls"),
        ]
    ).show()

    opticom_device_log.select(
        [
            count(when(col("gtt_opticom_log_id").isNull(), 1)).alias("nulls"),
            count(when(col("gtt_opticom_log_id").isNotNull(), 1)).alias("not nulls"),
        ]
    ).show()

    # events = vehicle_logs.join(vehicle_events, 'event_id').cache()
    # stop_events = events.join(stop_events, 'stop_event_id')
    # stop_events.select("vehicle_logs.*", "stop_events.*").show(n=10, truncate=False)


if __name__ == "__main__":
    opts = parse_args()
    run_job(opts)
