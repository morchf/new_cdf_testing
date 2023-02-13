CREATE EXTERNAL TABLE ext_gtfs.shapes (
  shape_id TEXT,
  shape_pt_lat DOUBLE PRECISION,
  shape_pt_lon DOUBLE PRECISION,
  shape_pt_sequence bigint,
  shape_dist_traveled DOUBLE PRECISION
)
PARTITIONED BY (agency TEXT, "date" TEXT)
STORED AS PARQUET
LOCATION 's3://{STATIC_GTFS_S3_BUCKET}/shapes/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
