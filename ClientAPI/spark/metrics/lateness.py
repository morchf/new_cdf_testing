import argparse
import pyspark
import pyspark.sql.functions as f


def main(*args):
    parser = argparse.ArgumentParser(description="`metrics/lateness` Spark job")
    parser.add_argument("--agency", help="E.g. 'sfmta'", required=True)
    parser.add_argument(
        "--date",
        help="E.g. '2018-05-01', '{2018-05-01,2018-05-02}', '2018-05-*'",
        required=True,
    )
    parser.add_argument("--input-bucket", help="E.g. 's3a://gtt-etl'", required=True)
    parser.add_argument("--output-bucket", help="E.g. 's3a://gtt-etl'", required=True)

    args = parser.parse_args(*args)
    if "{" in args.date:
        temp = args.date.split("{")[1].split("}")[0].split(",")
        dates = (temp[0], temp[-1])
    else:
        dates = (args.date, args.date)

    spark = (
        pyspark.sql.SparkSession.builder.appName("metrics/lateness")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    tsp_dataset = f"{args.input_bucket}/tsp_source_data/tsp_dataset"
    gtfs_dataset = f"{args.input_bucket}/gtfs"
    mindatecalc = (
        spark.read.options(basePath=f"{gtfs_dataset}/trips/agency={args.agency}")
        .parquet(f"{gtfs_dataset}/trips/agency={args.agency}")
        .withColumn(
            "datecalc",
            f.datediff(
                f.to_date(f.col("date"), "yyyy-MM-dd"),
                f.to_date(f.lit(dates[0]), "yyyy-MM-dd"),
            ),
        )
        .filter(f.col("datecalc") <= 0)
    )
    mindate = (
        mindatecalc.filter(
            f.col("datecalc") == mindatecalc.agg(f.max("datecalc")).collect()[0][0]
        )
        .select("date")
        .collect()[0][0]
        .strftime("%Y-%m-%d")
    )
    spark.read.options(
        basePath=f"{tsp_dataset}/stop_events/agency={args.agency}"
    ).parquet(
        f"{tsp_dataset}/stop_events/agency={args.agency}/date={args.date}"
    ).createOrReplaceTempView(
        "stop_events"
    )
    spark.read.options(basePath=f"{tsp_dataset}/trips/agency={args.agency}").parquet(
        f"{tsp_dataset}/trips/agency={args.agency}/date={args.date}"
    ).createOrReplaceTempView("trips")
    spark.read.options(
        basePath=f"{tsp_dataset}/vehicle_events/agency={args.agency}"
    ).parquet(
        f"{tsp_dataset}/vehicle_events/agency={args.agency}/date={args.date}"
    ).createOrReplaceTempView(
        "vehicle_events"
    )
    spark.read.options(
        basePath=f"{tsp_dataset}/vehicle_logs/agency={args.agency}"
    ).parquet(
        f"{tsp_dataset}/vehicle_logs/agency={args.agency}/date={args.date}"
    ).createOrReplaceTempView(
        "vehicle_logs"
    )

    spark.read.options(basePath=f"{gtfs_dataset}/trips/agency={args.agency}").parquet(
        f"{gtfs_dataset}/trips/agency={args.agency}"
    ).filter(
        (f.col("date") <= dates[1]) & (f.col("date") >= mindate)
    ).createOrReplaceTempView(
        "gtfs_trips"
    )
    spark.read.options(
        basePath=f"{gtfs_dataset}/stop_times/agency={args.agency}"
    ).parquet(f"{gtfs_dataset}/stop_times/agency={args.agency}").filter(
        (f.col("date") <= dates[1]) & (f.col("date") >= mindate)
    ).createOrReplaceTempView(
        "gtfs_stop_times"
    )
    spark.read.options(basePath=f"{gtfs_dataset}/stops/agency={args.agency}").parquet(
        f"{gtfs_dataset}/stops/agency={args.agency}"
    ).filter(
        (f.col("date") <= dates[1]) & (f.col("date") >= mindate)
    ).createOrReplaceTempView(
        "gtfs_stops"
    )
    vehicle_logs = spark.sql(
        """ 
    select vehicle_logs.`date`,
                vehicle_logs.gtt_trip_id,
                trips.tripID,
                vehicle_logs.gtt_opticom_log_id,
                vehicle_logs.`timestamp`,
                vehicle_logs.event_type,
                vehicle_logs.lat,
                vehicle_logs.lon,
                vehicle_logs.`timestamp`,
                vehicle_logs.event_id,
                gtfs_stop_times.stop_id,
                gtfs_stops.stop_name
    from vehicle_logs
        join trips using (`date`, gtt_trip_id)
        left join gtfs_stop_times on trips.tripID=gtfs_stop_times.trip_id
        join gtfs_stops using (stop_id)
        where vehicle_logs.event_type in ('TSP request', 'stop arrive', 'stop depart')
    """
    )
    vehicle_logs.createOrReplaceTempView("vehicle_logs")
    # vehicle_logs.show(5, False)

    # +----------+-------------------------+--------+------------------+-----------------------+-----------+---------+-----------+-----------------------+-------+------------------------------+------------------------------------+
    # |date      |gtt_trip_id              |tripID  |gtt_opticom_log_id|timestamp              |event_type |lat      |lon        |timestamp              |stop_id|stop_name                     |event_id                            |
    # +----------+-------------------------+--------+------------------+-----------------------+-----------+---------+-----------+-----------------------+-------+------------------------------+------------------------------------+
    # |2021-11-30|4010KW2054_20211130-t10_1|10301540|null              |2021-11-30 20:44:59.715|stop arrive|37.790935|-122.426085|2021-11-30 20:44:59.715|4015   |Clay St & Drumm St            |99788195-e999-49f1-a4a5-c9fa0abb267c|
    # |2021-11-30|4010KW2054_20211130-t10_1|10301540|null              |2021-11-30 20:44:59.715|stop arrive|37.790935|-122.426085|2021-11-30 20:44:59.715|6294   |Sacramento St & Davis St      |99788195-e999-49f1-a4a5-c9fa0abb267c|
    # |2021-11-30|4010KW2054_20211130-t10_1|10301540|null              |2021-11-30 20:44:59.715|stop arrive|37.790935|-122.426085|2021-11-30 20:44:59.715|6290   |Sacramento St & Battery St    |99788195-e999-49f1-a4a5-c9fa0abb267c|
    # |2021-11-30|4010KW2054_20211130-t10_1|10301540|null              |2021-11-30 20:44:59.715|stop arrive|37.790935|-122.426085|2021-11-30 20:44:59.715|6314   |Sacramento St & Sansome St    |99788195-e999-49f1-a4a5-c9fa0abb267c|
    # |2021-11-30|4010KW2054_20211130-t10_1|10301540|null              |2021-11-30 20:44:59.715|stop arrive|37.790935|-122.426085|2021-11-30 20:44:59.715|6307   |Sacramento St & Montgomery St |99788195-e999-49f1-a4a5-c9fa0abb267c|
    # +----------+-------------------------+--------+------------------+-----------------------+-----------+---------+-----------+-----------------------+-------+------------------------------+------------------------------------+

    # Added stopids by joining vehicle_events and stop_events tables.

    gd_events = spark.sql(
        """
        select vehicle_logs.`date`,
               vehicle_logs.gtt_trip_id,
               vehicle_logs.gtt_opticom_log_id,
               vehicle_logs.`timestamp`,
               vehicle_logs.event_type,
               vehicle_logs.lat,
               vehicle_logs.lon,
               trim(trips.routeName) as routeName,
               trips.direction,
               trim(vehicle_logs.stop_name) as stopName,
               vehicle_logs.stop_id,
               trips.tripID,
               -1 * stop_events.trackTime                                                                                as gd_lateness,
               sum(if(vehicle_logs.event_type = 'stop depart', 1, 0))
                   over (partition by (vehicle_logs.`date`, vehicle_logs.gtt_trip_id) order by vehicle_logs.`timestamp`) as gd_segment
        from vehicle_logs
                 join trips using (`date`, gtt_trip_id)
                 left join vehicle_events using (`date`, event_id)
                 left join stop_events using (`date`, stop_event_id)
        where vehicle_logs.event_type in ('TSP request', 'stop arrive', 'stop depart')
        and stop_events.stopName=vehicle_logs.stop_name
        """
    )
    gd_events.createOrReplaceTempView("gd_events")
    # gd_events.show(10, False)

    # +----------+-------------------------+------------------------------------+-----------------------+-----------+----------------+-----------------+---------+---------+------------------------------+-------+--------+-----------+----------+
    # |date      |gtt_trip_id              |gtt_opticom_log_id                  |timestamp              |event_type |lat             |lon              |routeName|direction|logsStopName                  |stop_id|tripID  |gd_lateness|gd_segment|
    # +----------+-------------------------+------------------------------------+-----------------------+-----------+----------------+-----------------+---------+---------+------------------------------+-------+--------+-----------+----------+
    # |2021-11-30|4010JY0862_20211130-t4_9R|016f9430-cbb3-4c9e-9aed-e43dceefc2e9|2021-11-30 10:18:07.472|stop arrive|37.7124616666667|-122.402513333333|9R       |outbound |Bayshore Blvd & Arleta Ave    |3772   |10315693|5          |0         |
    # |2021-11-30|4010JY0862_20211130-t4_9R|016f9430-cbb3-4c9e-9aed-e43dceefc2e9|2021-11-30 10:18:13.511|stop depart|37.7123933333333|-122.40265       |9R       |outbound |Bayshore Blvd & Arleta Ave    |3772   |10315693|5          |1         |
    # |2021-11-30|4010JY0862_20211130-t4_9R|a6f5adea-8b65-4adc-9778-e82e18d71b60|2021-11-30 10:19:21.515|stop arrive|37.711195       |-122.403823333333|9R       |outbound |Bayshore Blvd & Leland Ave    |3783   |10315693|6          |1         |
    # |2021-11-30|4010JY0862_20211130-t4_9R|a6f5adea-8b65-4adc-9778-e82e18d71b60|2021-11-30 10:19:22.549|stop depart|37.711095       |-122.4039        |9R       |outbound |Bayshore Blvd & Leland Ave    |3783   |10315693|6          |2         |
    # |2021-11-30|4010JY0862_20211130-t4_9R|null                                |2021-11-30 10:28:52.881|stop arrive|37.7141233333333|-122.423713333333|9R       |outbound |Sunnydale Ave / McLaren School|6574   |10315693|5          |2         |
    # +----------+-------------------------+------------------------------------+-----------------------+-----------+----------------+-----------------+---------+---------+------------------------------+-------+--------+-----------+----------+

    gd_lateness = spark.sql(
        """
        select first(`date`)                                                    as `date`,
               first(routeName)                                                 as Route,
               first(direction)                                                 as Direction,
               first(if(event_type = 'stop depart', stopName, null), true)      as StopStart,
               first(if(event_type = 'stop depart', stop_id, null), true)      as StopStartId,
               first(if(event_type = 'stop depart', `timestamp`, null), true)   as StopStartTime,
               first(if(event_type = 'stop depart', gd_lateness, null), true)   as StopStartLateness,
               first(if(event_type = 'stop depart', lat, null), true)           as StopStartLatitude,
               first(if(event_type = 'stop depart', lon, null), true)           as StopStartLongitude,
               first(if(event_type = 'stop arrive', stopName, null), true)      as StopEnd,
               first(if(event_type = 'stop arrive', stop_id, null), true)      as StopEndId,
               first(if(event_type = 'stop arrive', `timestamp`, null), true)   as StopEndTime,
               first(if(event_type = 'stop arrive', gd_lateness, null), true)   as StopEndLateness,
               first(if(event_type = 'stop arrive', lat, null), true)           as StopEndLatitude,
               first(if(event_type = 'stop arrive', lon, null), true)           as StopEndLongitude,
               count(gtt_opticom_log_id)                                        as NumIntersections,
               1                                                                as VehiclePassThrough,
               sum(if(event_type = 'TSP request', 1, 0))                        as NumRequests,
               (first(if(event_type = 'stop depart', gd_lateness, null), true) -
                first(if(event_type = 'stop arrive', gd_lateness, null), true)) as LatenessReduction
        from gd_events
        group by `date`, gtt_trip_id, gd_segment
        having sum(if(event_type = 'stop arrive', 1, 0)) > 0
           and sum(if(event_type = 'stop depart', 1, 0)) > 0
        """
    )
    # +----------+-----+---------+--------------------------+---------------------------------+-----------+-----------------------+-----------------+-----------------+------------------+----------------------------+---------+-----------------------+---------------+----------------+-----------------+----------------+------------------+-----------+-----------------+
    # |date      |Route|Direction|gtt_trip_id               |StopStart                        |StopStartId|StopStartTime          |StopStartLateness|StopStartLatitude|StopStartLongitude|StopEnd                     |StopEndId|StopEndTime            |StopEndLateness|StopEndLatitude |StopEndLongitude |NumIntersections|VehiclePassThrough|NumRequests|LatenessReduction|
    # +----------+-----+---------+--------------------------+---------------------------------+-----------+-----------------------+-----------------+-----------------+------------------+----------------------------+---------+-----------------------+---------------+----------------+-----------------+----------------+------------------+-----------+-----------------+
    # |2021-11-30|9R   |inbound  |4010JY0862_20211130-t10_9R|Bayshore Blvd & Visitacion Ave   |3793       |2021-11-30 13:19:28.331|-1               |37.71063         |-122.403886666667 |Bayshore Blvd & Cortland Ave|3778     |2021-11-30 13:31:57.456|-3             |37.7398766666667|-122.406873333333|0               |1                 |0          |2                |
    # |2021-11-30|19   |inbound  |4010JZ0877_20211130-t17_19|Middle Point Rd & West Point Rd  |5503       |2021-11-30 14:34:27.808|-1               |37.737025        |-122.37941        |Evans Ave & Newhall St      |4555     |2021-11-30 14:36:44.308|-2             |37.7419566666667|-122.386305      |0               |1                 |0          |1                |
    # |2021-11-30|19   |outbound |4010JZ0877_20211130-t19_19|EVANS AVE/Opposite US Post Office|4564       |2021-11-30 16:37:24.645|-1               |37.7395833333333 |-122.382585       |Middle Point & Acacia       |7719     |2021-11-30 16:38:11.488|-1             |37.7370983333333|-122.379493333333|0               |1                 |0          |0                |
    # |2021-11-30|19   |inbound  |4010JZ0877_20211130-t22_19|Middle Point Rd & West Point Rd  |5503       |2021-11-30 17:05:57.525|0                |37.7370583333333 |-122.379405       |Evans Ave & Newhall St      |4555     |2021-11-30 17:09:07.051|1              |37.7419533333333|-122.386333333333|0               |1                 |0          |-1               |
    # |2021-11-30|19   |inbound  |4010JZ0877_20211130-t27_19|Townsend St & 7th St             |7960       |2021-11-30 19:54:21.636|0                |37.7712016666667 |-122.402293333333 |Geary St & Larkin St        |4302     |2021-11-30 20:09:46.758|-1             |37.7860383333333|-122.418163333333|0               |1                 |0          |1                |
    # +----------+-----+---------+--------------------------+---------------------------------+-----------+-----------------------+-----------------+-----------------+------------------+----------------------------+---------+-----------------------+---------------+----------------+-----------------+----------------+------------------+-----------+-----------------+

    gd_lateness.show(10, False)
    gd_lateness.repartition(1, "date").write.partitionBy("date").save(
        format="parquet",
        mode="overwrite",
        path=f"{args.output_bucket}/lateness/lateness_source_data/agency={args.agency}",
    )


if __name__ == "__main__":
    main()
