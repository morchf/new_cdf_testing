CREATE
OR REPLACE PROCEDURE sp_vehicle_logs__interpolated () AS $$ BEGIN
  RAISE INFO 'Interpolating \'vehicle_logs\'';

DROP TABLE IF EXISTS staging__day_seconds;

CREATE TEMP TABLE staging__day_seconds AS
SELECT
  (
    (
      SELECT
        MAX(trip_start_date)
      FROM
        staging__vehicle_logs
    ) :: DATE
  ) + s AS "timestamp"
FROM
  v_seconds
ORDER BY
  1;

DROP TABLE IF EXISTS staging__low_resolution_trip_instance_ids;

CREATE TEMP TABLE staging__low_resolution_trip_instance_ids AS WITH low_resolution_counts AS (
  SELECT
    SUM((source_device <> 'RT_GTFS') :: INT) AS num_high_resolution,
    agency_id,
    trip_instance_id
  FROM
    staging__vehicle_logs
  GROUP BY
    agency_id,
    trip_instance_id
)
SELECT
  agency_id,
  trip_instance_id
FROM
  low_resolution_counts
WHERE
  num_high_resolution = 0;

-- Copy and truncate existing 'staging__vehicle_logs' table
DROP TABLE IF EXISTS staging__vehicle_logs__copy;

CREATE TEMP TABLE staging__vehicle_logs__copy AS
SELECT
  vl. *
FROM
  staging__vehicle_logs vl
  INNER JOIN staging__low_resolution_trip_instance_ids lrt ON vl.agency_id = lrt.agency_id
  AND vl.trip_instance_id = lrt.trip_instance_id;

DROP TABLE IF EXISTS staging__vehicle_logs__high_resolution_copy;

CREATE TEMP TABLE staging__vehicle_logs__high_resolution_copy AS
SELECT
  vl. *
FROM
  staging__vehicle_logs vl
  LEFT OUTER JOIN staging__low_resolution_trip_instance_ids lrt ON vl.agency_id = lrt.agency_id
  AND vl.trip_instance_id = lrt.trip_instance_id;

DROP TABLE staging__vehicle_logs;

CREATE TEMP TABLE staging__vehicle_logs AS
SELECT
  agency_id,
  entity_id,
  current_stop_sequence,
  rt_stop_id,
  current_status,
  congestion_level,
  occupancy_status,
  vehicle_id,
  vehicle_label,
  license_plate,
  bearing,
  odometer,
  speed,
  trip_id,
  route_id,
  trip_direction_id,
  trip_start_time,
  trip_start_date,
  schedule_relationship,
  trip_instance_id,
  source_device,
  latitude,
  longitude,
  "timestamp"
FROM
  staging__vehicle_logs__high_resolution_copy;

-- Interpolate
DROP TABLE IF EXISTS staging__vehicle_logs_interpolated;

CREATE TEMP TABLE staging__vehicle_logs_interpolated AS WITH gps AS (
  SELECT
    *,
    LEAD("timestamp") OVER (
      PARTITION BY agency_id,
      trip_instance_id
      ORDER BY
        "timestamp"
    ) AS next_timestamp,
    LEAD(latitude) OVER (
      PARTITION BY agency_id,
      trip_instance_id
      ORDER BY
        "timestamp"
    ) AS next_latitude,
    LEAD(longitude) OVER (
      PARTITION BY agency_id,
      trip_instance_id
      ORDER BY
        "timestamp"
    ) AS next_longitude
  FROM
    staging__vehicle_logs__copy
)
SELECT
  g.agency_id,
  g.entity_id,
  g.current_stop_sequence,
  g.rt_stop_id,
  g.current_status,
  g.congestion_level,
  g.occupancy_status,
  g.vehicle_id,
  g.vehicle_label,
  g.license_plate,
  g.bearing,
  g.odometer,
  g.speed,
  g.trip_id,
  g.route_id,
  g.trip_direction_id,
  g.trip_start_time,
  g.trip_start_date,
  g.schedule_relationship,
  g.trip_instance_id,
  g.source_device || '-INTERPOLATED' AS source_device,
  g.next_timestamp,
  g.next_latitude,
  g.next_longitude,
  f_interpolate_linear(
    ds.timestamp,
    g.timestamp,
    g.latitude,
    g.longitude,
    0 :: FLOAT,
    0 :: FLOAT,
    g.next_timestamp,
    g.next_latitude,
    g.next_longitude,
    0 :: FLOAT,
    0 :: FLOAT
  ) AS attr,
  f_at(attr, 0) :: FLOAT AS latitude,
  f_at(attr, 1) :: FLOAT AS longitude,
  ds.timestamp
FROM
  gps g
  JOIN staging__day_seconds ds ON ds.timestamp BETWEEN g.timestamp
  AND g.next_timestamp;

-- Copy over interpolated values
INSERT INTO
  staging__vehicle_logs
SELECT
  agency_id,
  entity_id,
  current_stop_sequence,
  rt_stop_id,
  current_status,
  congestion_level,
  occupancy_status,
  vehicle_id,
  vehicle_label,
  license_plate,
  bearing,
  odometer,
  speed,
  trip_id,
  route_id,
  trip_direction_id,
  trip_start_time,
  trip_start_date,
  schedule_relationship,
  trip_instance_id,
  source_device,
  latitude,
  longitude,
  "timestamp"
FROM
  staging__vehicle_logs_interpolated;

END;

$$ LANGUAGE plpgsql;