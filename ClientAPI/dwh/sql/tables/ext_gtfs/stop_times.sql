CREATE EXTERNAL TABLE ext_gtfs.stop_times (
  trip_id TEXT,
  arrival_time TEXT,
  departure_time TEXT,
  stop_id TEXT,
  stop_sequence bigint,
  stop_headsign TEXT,
  pickup_type bigint,
  drop_off_type bigint,
  continuous_pickup bigint,
  continuous_drop_off bigint,
  shape_dist_traveled DOUBLE PRECISION,
  timepoint bigint
)
PARTITIONED BY (agency TEXT, "date" TEXT)
STORED AS PARQUET
LOCATION 's3://{STATIC_GTFS_S3_BUCKET}/stop_times/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
