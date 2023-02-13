DROP TABLE ext_tsp.rt_gtfs_merged_vehicle_positions;

CREATE EXTERNAL TABLE ext_tsp.rt_gtfs_merged_vehicle_positions PARTITIONED BY
  (
    agency_id,
    utc_date)
  STORED AS PARQUET LOCATION 's3://gtt-etl-dev/gtfs-realtime/merged_vehicle_positions' TABLE PROPERTIES (
    'write.parallel' = 'off'
) AS
  SELECT
    *
  FROM
    ext_tsp.rt_gtfs_vehicle_positions
  WHERE
    utc_date = '2022-06-10'
    AND "timestamp" <> 0
  ORDER BY
    "timestamp" ASC
    --  WHERE agency_id = '0537199e-e853-11ec-a8b8-f65b686c7d91/'
