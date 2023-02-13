CREATE EXTERNAL TABLE ext_evp.intersections (
  "Name" TEXT,
  "Location Id" TEXT,
  "Latitude" TEXT,
  "Longitude" TEXT,
  "Cabinet" TEXT,
  "Controller" TEXT,
  "Int. #" TEXT,
  "Controller LAN IP" TEXT,
  "Make" TEXT,
  "Model" TEXT,
  "Signal Core Serial #" TEXT,
  "764 Serial #" TEXT,
  "LAN IP" TEXT,
  "Miovision ID" TEXT,
  "764 Configured" TEXT,
  "Approach threshold adjusted" TEXT,
  "Notes" TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION 's3://{EVP_S3_PATH}/evp_intersections'
TABLE PROPERTIES ('skip.header.line.count' = '1')
-- LOCATION '{INTERSECTIONS_S3_PATH}'
