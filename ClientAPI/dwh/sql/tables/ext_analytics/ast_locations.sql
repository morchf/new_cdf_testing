-- location
CREATE EXTERNAL TABLE ext_analytics.ast_locations (
  city TEXT,
  "state" TEXT,
  street TEXT,
  "address" TEXT,
  latitude TEXT,
  longitude TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION 's3://{ASSET_S3_BUCKET}/locations/'
TABLE PROPERTIES ('skip.header.line.count' = '1')