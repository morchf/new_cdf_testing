CREATE
OR REPLACE PROCEDURE testing.sp_fixture__travel_time () AS $$ BEGIN
  DROP TABLE IF EXISTS staging__vehicle_logs;

CREATE TEMP TABLE staging__vehicle_logs (
  gtt_opticom_log_id TEXT,
  gtt_vehicle_log_id TEXT,
  gtt_trip_id TEXT,
  event_id TEXT,
  event_type TEXT,
  serialnumber TEXT,
  rssi TEXT,
  vehiclemode TEXT,
  vehiclegpscstat TEXT,
  vehiclegpscsatellites TEXT,
  opstatus TEXT,
  turnstatus TEXT,
  vehicleclass TEXT,
  conditionalpriority TEXT,
  vehiclediagnosticvalue TEXT,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  speed TEXT,
  heading TEXT,
  TIMESTAMP TIMESTAMP,
  agency TEXT,
  DATE TEXT
);

-- Load data for trip 4010KP2018_20210902-t4_29
COPY staging__vehicle_logs
FROM
  's3://gtt-gd-artifacts-dev/dwh/sql/test/data/vehicle_logs.csv' iam_role 'arn:aws:iam::083011521439:role/AWSDataWarehouseRole-dev' CSV IGNOREHEADER 1;

DELETE FROM
  staging__vehicle_logs
WHERE
  event_type <> 'GPS';

-- Dependency tables
CALL sp_mock_table(
  'mv_gtfs_dates',
  '(agency TEXT, "date" TEXT, gtfs_date TEXT)'
);

INSERT INTO
  mv_gtfs_dates (agency, "date", gtfs_date)
VALUES
  ('testagency', '2021-09-02', '2021-09-01');

CALL sp_mock_table(
  'mv_trips',
  '(agency TEXT, "date" TEXT, routeName TEXT, gtt_trip_id TEXT, direction TEXT, tripid TEXT)'
);

INSERT INTO
  mv_trips (
    agency,
    "date",
    routeName,
    gtt_trip_id,
    direction,
    tripid
  )
VALUES
  (
    'testagency',
    '2021-09-02',
    '29',
    '4010KP2018_20210902-t4_29',
    'outbound',
    '10173384'
  );

CALL sp_mock_table(
  'mv_gtfs_stops',
  '(
      route TEXT,
      agency TEXT,
      date TEXT,
      route_id TEXT,
      stop_id TEXT,
      stop_name TEXT,
      stop_lat TEXT,
      stop_lon TEXT,
      direction_id TEXT,
      stop_sequence TEXT,
      trip_id TEXT,
      repeat_stop_order TEXT,
      route_short_name TEXT,
      route_long_name TEXT
    )'
);

COPY mv_gtfs_stops
FROM
  's3://gtt-gd-artifacts-dev/dwh/sql/test/data/mv_gtfs_stops.csv' iam_role 'arn:aws:iam::083011521439:role/AWSDataWarehouseRole-dev' CSV IGNOREHEADER 1;

CALL sp_mock_table(
  'mv_intersection_dates',
  '(agency TEXT, "date" TEXT, intersection_date TEXT)'
);

INSERT INTO
  mv_intersection_dates (agency, "date", intersection_date)
VALUES
  ('testagency', '2021-09-02', '2021-09-01');

CALL sp_mock_table(
  'route_to_intersection_mapping',
  '(LIKE route_to_intersection_mapping)'
);

COPY route_to_intersection_mapping
FROM
  's3://gtt-gd-artifacts-dev/dwh/sql/test/data/route_to_intersection_mapping.csv' iam_role 'arn:aws:iam::083011521439:role/AWSDataWarehouseRole-dev' CSV IGNOREHEADER 1;

END;

$$ LANGUAGE plpgsql;