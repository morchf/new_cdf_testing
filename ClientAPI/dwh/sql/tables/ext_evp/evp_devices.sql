CREATE EXTERNAL TABLE ext_evp.devices (
  "Public IP" TEXT,
  "Description" TEXT,
  "Agency" TEXT,
  "Device Serial Number" TEXT,
  "GTT Serial Number (Create by Ops for MP-70)" TEXT,
  "LAN IP" TEXT,
  "Make" TEXT,
  "Model" TEXT,
  "IMEI" TEXT,
  "MAC Address" TEXT,
  "Factory Default PW" TEXT,
  "Sim Serial Number" TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION 's3://{EVP_S3_PATH}/evp_devices'
TABLE PROPERTIES ('skip.header.line.count' = '1')

