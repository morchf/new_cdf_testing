CREATE
OR REPLACE PROCEDURE testing.sp_fixture__dwell_time__single_stop () AS $$ BEGIN
  RAISE INFO 'Staging vehicle logs';

DROP TABLE IF EXISTS staging__vehicle_logs;

CREATE TEMP TABLE staging__vehicle_logs (
  lon DOUBLE PRECISION,
  lat DOUBLE PRECISION,
  serialnumber TEXT,
  gtt_trip_id TEXT,
  TIMESTAMP TIMESTAMP,
  speed TEXT,
  gtt_vehicle_log_id TEXT,
  gtt_opticom_log_id TEXT,
  event_id TEXT,
  event_type TEXT,
  rssi TEXT,
  vehiclemode TEXT,
  vehiclegpscstat TEXT,
  vehiclegpscsatellites TEXT,
  opstatus TEXT,
  turnstatus TEXT,
  vehicleclass TEXT,
  conditionalpriority TEXT,
  vehiclediagnosticvalue TEXT,
  heading TEXT,
  agency TEXT,
  "DATE" TEXT
);

COPY staging__vehicle_logs
FROM
  's3://gtt-gd-artifacts-dev/dwh/sql/test/data/vehicle_logs__single_vehicle.csv' iam_role 'arn:aws:iam::083011521439:role/AWSDataWarehouseRole-dev' CSV IGNOREHEADER 1 FILLRECORD;

UPDATE
  staging__vehicle_logs
SET
  event_type = 'GPS',
  agency = 'testagency',
  "DATE" = '2022-03-14';

RAISE INFO 'Mocking stop dates';

-- Dependency tables
CALL sp_mock_table(
  'mv_gtfs_dates',
  '(agency TEXT, "date" TEXT, gtfs_date TEXT)'
);

INSERT INTO
  mv_gtfs_dates (agency, "date", gtfs_date)
VALUES
  ('testagency', '2022-03-14', '2022-03-05');

RAISE INFO 'Mocking trips';

CALL sp_mock_table(
  'mv_trips',
  '(agency TEXT, "date" TEXT, routeName TEXT, direction TEXT, gtt_trip_id TEXT, tripid TEXT)'
);

INSERT INTO
  mv_trips (
    agency,
    "date",
    routeName,
    direction,
    gtt_trip_id,
    tripid
  )
VALUES
  (
    'testagency',
    '2022-03-14',
    '5',
    'inbound',
    '4010KK1211_20220314-t32_5',
    '10518643'
  ),
  (
    'testagency',
    '2022-03-14',
    '5',
    'inbound',
    '4010KK1204_20220314-t11_5',
    '10518643'
  ),
  (
    'testagency',
    '2022-03-14',
    '5',
    'inbound',
    '4010KK1191_20220314-t29_5',
    '10518643'
  ),
  (
    'testagency',
    '2022-03-14',
    '5',
    'inbound',
    '4010KR2035_20220314-t13_5',
    '10518643'
  ),
  (
    'testagency',
    '2022-03-14',
    '5',
    'inbound',
    '4010KK1173_20220314-t7_5',
    '10518643'
  );

RAISE INFO 'Mocking GTFS stops';

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
      route_long_name TEXT,
      num_repeats BIGINT
    )'
);

INSERT INTO
  mv_gtfs_stops (
    "route",
    agency,
    "date",
    route_id,
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    direction_id,
    stop_sequence,
    trip_id,
    repeat_stop_order,
    route_short_name,
    route_long_name,
    num_repeats
  )
VALUES
  (
    '5',
    'testagency',
    '2022-03-05',
    'route_5',
    '5390',
    'Mcallister St & Divisadero St',
    37.77773,
    -122.43851,
    1,
    28,
    '10518643',
    0,
    '5',
    'Route 5',
    0
  );

CALL testing.sp_mock_mv('mv_gtfs_segments');

RAISE INFO 'Mocking intersections';

CALL sp_mock_table(
  'mv_intersection_dates',
  '(agency TEXT, "date" TEXT, intersection_date TEXT)'
);

CALL sp_mock_table(
  'mv_intersections',
  '(agency TEXT, "date" TEXT, deviceid TEXT, locationid TEXT, locationname TEXT)'
);

CALL sp_mock_table(
  'route_to_intersection_mapping',
  '(LIKE route_to_intersection_mapping)'
);

END;

$$ LANGUAGE plpgsql;