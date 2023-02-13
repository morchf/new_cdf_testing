CREATE EXTERNAL TABLE ext_tsp.cvp_vehicle_logs (
  gtt_opticom_log_id TEXT,
  gtt_vehicle_log_id TEXT,
  gtt_trip_id TEXT,
  event_id TEXT,
  event_type TEXT,
  serialnumber INTEGER,
  rssi INTEGER,
  vehiclemode INTEGER,
  vehiclegpscstat INTEGER,
  vehiclegpscsatellites INTEGER,
  opstatus INTEGER,
  turnstatus INTEGER,
  vehicleclass INTEGER,
  conditionalpriority INTEGER,
  vehiclediagnosticvalue INTEGER,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  speed DOUBLE PRECISION,
  heading DOUBLE PRECISION,
  "timestamp" TIMESTAMP
)
PARTITIONED BY (agency TEXT, "date" TEXT) 
STORED AS PARQUET
LOCATION 's3://{CVP_S3_PATH}/vehicle_logs/'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
