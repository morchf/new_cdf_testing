CREATE EXTERNAL TABLE ext_gtfs.routes (
  route_id TEXT,
  agency_id TEXT,
  route_short_name TEXT,
  route_long_name TEXT,
  route_desc TEXT,
  route_type bigint,
  route_url TEXT,
  route_color TEXT,
  route_text_color TEXT,
  route_sort_order bigint,
  continuous_pickup bigint,
  continuous_drop_off bigint
)
PARTITIONED BY (agency TEXT, "date" TEXT)
STORED AS PARQUET
LOCATION 's3://{STATIC_GTFS_S3_BUCKET}/routes/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
