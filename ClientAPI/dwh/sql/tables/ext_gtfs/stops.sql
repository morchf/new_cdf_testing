CREATE EXTERNAL TABLE ext_gtfs.stops (
  stop_id TEXT,
  stop_code TEXT,
  stop_name TEXT,
  tts_stop_name TEXT,
  stop_desc TEXT,
  stop_lat DOUBLE PRECISION,
  stop_lon DOUBLE PRECISION,
  zone_id TEXT,
  stop_url TEXT,
  location_type bigint,
  parent_station TEXT,
  stop_timezone TEXT,
  wheelchair_boarding bigint,
  level_id TEXT,
  platform_code TEXT
)
PARTITIONED BY (agency TEXT, "date" TEXT)
STORED AS PARQUET
LOCATION 's3://{STATIC_GTFS_S3_BUCKET}/stops/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
