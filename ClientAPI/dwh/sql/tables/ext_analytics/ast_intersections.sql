-- location
CREATE EXTERNAL TABLE ext_analytics.ast_intersections (
  FID TEXT,
  OID_ TEXT,
  "Signal Location" TEXT,
  "Owner" TEXT,
  Municipality TEXT,
  County TEXT,
  "BRT Line" TEXT,
  "TSP Type" TEXT,
  "TSP Status" TEXT,
  "Comm. Type" TEXT,
  "Controller Type" TEXT,
  "Existing Miovision Equipment" TEXT,
  "GTT Equipment needed" TEXT,
  "GTT/NE Signal Installation" TEXT,
  "Miovision Equipment" TEXT,
  "Miovision Comms" TEXT,
  "NE Signal Installs" TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION 's3://{ASSET_S3_BUCKET}/intersections/'
TABLE PROPERTIES ('skip.header.line.count' = '1')
