CREATE EXTERNAL TABLE ext_evp.incidents (
  "EventNumber" TEXT,
  "DispatchNumber" TEXT,
  "Unit" TEXT,
  "Dispatched" TEXT,
  "Enroute" TEXT,
  "Arrival" TEXT,
  "EnrouteToHospital" TEXT,
  "HospitalArrival" TEXT,
  "ClearTime" TEXT,
  "Location" TEXT,
  "Municipality" TEXT,
  "Latitude" TEXT,
  "Longitude" TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION 's3://{EVP_S3_PATH}/evp_incidents'
TABLE PROPERTIES ('skip.header.line.count' = '1')
