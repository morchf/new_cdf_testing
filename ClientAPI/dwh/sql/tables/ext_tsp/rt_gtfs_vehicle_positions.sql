CREATE EXTERNAL TABLE ext_tsp.rt_gtfs_vehicle_positions (
  entity_id TEXT,
  "timestamp" TEXT,
  current_stop_sequence TEXT,
  stop_id TEXT,
  current_status TEXT,
  congestion_level TEXT,
  occupancy_status TEXT,
  vehicle_id TEXT,
  vehicle_label TEXT,
  license_plate TEXT,
  latitude TEXT,
  longitude TEXT,
  bearing TEXT,
  odometer TEXT,
  speed TEXT,
  trip_id TEXT,
  route_id TEXT,
  trip_direction_id TEXT,
  trip_start_time TEXT,
  trip_start_date TEXT,
  schedule_relationship TEXT
)
PARTITIONED BY (agency_id TEXT, utc_date TEXT) 
STORED AS PARQUET
LOCATION 's3://{RT_GTFS_VEHICLE_POSITIONS_S3_PATH}'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
