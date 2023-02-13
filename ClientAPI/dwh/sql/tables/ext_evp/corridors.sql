CREATE EXTERNAL TABLE ext_evp.corridors (
  corridor_id TEXT,
  corridor_name TEXT,
  "sequence" BIGINT,
  location_id TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION 's3://{EVP_S3_PATH}/evp_corridors'
TABLE PROPERTIES ('skip.header.line.count' = '1')
