CREATE EXTERNAL TABLE ext_analytics.rt_radio_messages (
  CMSId TEXT,
  GTTSerial TEXT,
  UnitId INT,
  RSSI INT,
  Latitude FLOAT,
  Longitude FLOAT,
  Heading INT,
  Speed FLOAT,
  VehicleGPSCStat INT,
  VehicleGPSCSatellites INT,
  VehicleVID INT,
  AgencyCode INT,
  VehicleModeStatus INT,
  VehicleTurnStatus INT,
  VehicleOpStatus INT,
  VehicleClass INT,
  ConditionalPriority INT,
  VehicleDiagnosticValue FLOAT,
  VehicleName TEXT,
  DeviceName TEXT,
  device_timestamp TEXT,
  ioT_timestamp TEXT,
  OriginalRTRadioMsg TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT, source_device TEXT)
STORED AS PARQUET
LOCATION 's3://{RT_RADIO_S3_BUCKET}/./'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
