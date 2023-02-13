import argparse
import datetime

import pyspark
from pyspark.sql import functions as f
from pyspark.sql.functions import acos, col, cos, lit, sin, toRadians


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


def main():
    parser = argparse.ArgumentParser(
        description="`metrics/route_to_intersection` Spark job"
    )
    parser.add_argument("--agency", help="E.g. 'sfmta'", required=True)
    parser.add_argument(
        "--date",
        help="E.g. '2018-05-01', '{2018-05-01,2018-05-02}', '2018-05-*'",
        required=True,
    )
    parser.add_argument("--input-bucket", help="E.g. 's3a://gtt-etl'", required=True)
    parser.add_argument("--output-bucket", help="E.g. 's3a://gtt-etl'", required=True)
    args = parser.parse_args()

    spark = (
        pyspark.sql.SparkSession.builder.appName("metrics/route_to_intersection")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    tsp_dataset = f"{args.input_bucket}/tsp_source_data/tsp_dataset"
    gtfs_dataset = f"{args.input_bucket}/gtfs"

    source_dates = spark.read.parquet(f"{gtfs_dataset}/routes/agency={args.agency}")
    source_min_date = source_dates.select("date").agg({"date": "min"}).collect()[0][0]
    source_dates_2 = spark.read.parquet(
        f"{tsp_dataset}/device_configuration/agency={args.agency}"
    )
    source_min_date_2 = (
        source_dates_2.select("date").agg({"date": "min"}).collect()[0][0]
    )

    source_date = max(source_min_date, source_min_date_2)

    try:
        target_max_date = (
            spark.read.parquet(
                f"{args.output_bucket}/route_to_intersection/route_to_intersection_mapping/agency={args.agency}"
            )
            .agg({"date": "max"})
            .collect()[0][0]
        )
    except:
        target_max_date = source_date - datetime.timedelta(1)
    end_date = min(
        datetime.datetime.today().date(), target_max_date + datetime.timedelta(180)
    )

    gtfs_routes = (
        spark.read.options(basePath=f"{gtfs_dataset}/routes/agency={args.agency}")
        .parquet(f"{gtfs_dataset}/routes/agency={args.agency}")
        .where(col("date") > target_max_date)
        .where(col("date") <= end_date)
        .alias("gtfs_routes")
    )
    gtfs_routes.createOrReplaceTempView("gtfs_routes")
    gtfs_trips = (
        spark.read.options(basePath=f"{gtfs_dataset}/trips/agency={args.agency}")
        .parquet(f"{gtfs_dataset}/trips/agency={args.agency}")
        .where(col("date") > target_max_date)
        .where(col("date") <= end_date)
        .alias("gtfs_trips")
    )
    gtfs_trips.createOrReplaceTempView("gtfs_trips")
    gtfs_shapes = (
        spark.read.options(basePath=f"{gtfs_dataset}/shapes/agency={args.agency}")
        .parquet(f"{gtfs_dataset}/shapes/agency={args.agency}")
        .where(col("date") > target_max_date)
        .where(col("date") <= end_date)
        .alias("gtfs_shapes")
    )
    gtfs_shapes.createOrReplaceTempView("gtfs_shapes")
    device_configuration = (
        spark.read.options(
            basePath=f"{tsp_dataset}/device_configuration/agency={args.agency}"
        )
        .parquet(f"{tsp_dataset}/device_configuration/agency={args.agency}")
        .where(col("date") > target_max_date)
        .where(col("date") <= end_date)
        .alias("device_configuration")
        .repartition("deviceid")
    )
    device_configuration = device_configuration.select(
        "deviceconfigurationid",
        "deviceid",
        "createddatetime",
        "createduserid",
        "isdeleted",
        "lastobserveddate",
        "channelaname",
        "channelbname",
        "channelcname",
        "channeldname",
        "channelanotused",
        "channelbnotused",
        "channelcnotused",
        "channeldnotused",
        "archiveddate",
        "date_ran",
        "lat",
        "lon",
        "date",
    )
    device_configuration.createOrReplaceTempView("device_configuration")

    device_configuration_dates = spark.sql(
        """
        select distinct `date` as device_configuration_date
        from device_configuration
        """
    )
    device_configuration_dates.createOrReplaceTempView("device_configuration_dates")

    gtfs_dates = spark.sql(
        """
        select distinct `date` as gtfs_date
        from gtfs_routes
        """
    )
    gtfs_dates.createOrReplaceTempView("gtfs_dates")

    date_diffs = spark.sql(
        """
        select *, datediff(to_date(device_configuration_date), to_date(gtfs_date)) as date_diff
        from device_configuration_dates cross join gtfs_dates
        where device_configuration_date > gtfs_date
        """
    )
    date_diffs.createOrReplaceTempView("date_diffs")

    date_mapping = spark.sql(
        """
        select gtfs_date, device_configuration_date
        from date_diffs join (
            select gtfs_date, min(date_diff) as min_date_diff
            from date_diffs
            group by gtfs_date
        ) using(gtfs_date)
        where date_diff = min_date_diff
        """
    ).alias("date_mapping")
    date_mapping.createOrReplaceTempView("date_mapping")

    gtfs_merged = spark.sql(
        """
        select distinct route_id, trim(route_short_name) as route_short_name, direction_id, shape_id, `date`
        from gtfs_routes
            join gtfs_trips using (`date`, route_id)
        """
    )
    gtfs_merged.createOrReplaceTempView("gtfs_merged")

    gtfs_merged_shapes = (
        spark.sql(
            """
        select *, shape_pt_lat, shape_pt_lon, shape_pt_sequence
        from gtfs_merged
            join gtfs_shapes using (`date`, shape_id)
        """
        )
        .repartition("route_id")
        .alias("gtfs_merged_shapes")
    )
    gtfs_merged_shapes.createOrReplaceTempView("gtfs_merged_shapes")

    route_to_intersection = (
        device_configuration.join(
            date_mapping,
            on=[
                col("date_mapping.device_configuration_date")
                == col("device_configuration.date")
            ],
            how="inner",
        )
        .join(
            gtfs_merged_shapes,
            on=[col("gtfs_merged_shapes.date") == col("date_mapping.gtfs_date")],
        )
        .repartition("route_id")
        .filter(
            haversine(col("lat"), col("lon"), col("shape_pt_lat"), col("shape_pt_lon"))
            < 30
        )
        .groupBy(
            "route_id", "route_short_name", "direction_id", "deviceid", "gtfs_date"
        )
        .agg(
            f.min("lat").alias("latitude"),
            f.min("lon").alias("longitude"),
            f.min("shape_pt_sequence").alias("sequence"),
        )
        .select(
            "route_id",
            "route_short_name",
            "direction_id",
            "deviceid",
            "latitude",
            "longitude",
            "sequence",
            col("gtfs_date").alias("date"),
        )
        .alias("route_to_intersection")
    )

    route_to_intersection.repartition(1, "date").write.partitionBy("date").save(
        format="parquet",
        mode="overwrite",
        path=f"{args.output_bucket}/route_to_intersection/route_to_intersection_mapping/agency={args.agency}",
    )


if __name__ == "__main__":
    main()
