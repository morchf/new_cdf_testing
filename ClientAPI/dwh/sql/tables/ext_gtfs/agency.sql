CREATE EXTERNAL TABLE ext_gtfs.agency (
  agency_id TEXT,
  agency_name TEXT,
  agency_url TEXT,
  agency_timezone TEXT,
  agency_lang TEXT,
  agency_phone TEXT,
  agency_fare_url TEXT,
  agency_email TEXT
)
PARTITIONED BY (agency TEXT, "date" TEXT)
STORED AS PARQUET
LOCATION 's3://{STATIC_GTFS_S3_BUCKET}/agency/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
