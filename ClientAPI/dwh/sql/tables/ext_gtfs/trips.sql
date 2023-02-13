CREATE EXTERNAL TABLE ext_gtfs.trips (
  route_id TEXT,
  service_id TEXT,
  trip_id TEXT,
  trip_headsign TEXT,
  trip_short_name TEXT,
  direction_id bigint,
  block_id TEXT,
  shape_id TEXT,
  wheelchair_accessible bigint,
  bikes_allowed bigint
)
PARTITIONED BY (agency TEXT, "date" TEXT)
STORED AS PARQUET
LOCATION 's3://{STATIC_GTFS_S3_BUCKET}/trips/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
