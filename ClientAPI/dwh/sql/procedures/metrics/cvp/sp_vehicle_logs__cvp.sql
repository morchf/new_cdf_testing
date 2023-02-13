CREATE OR REPLACE PROCEDURE sp_vehicle_logs__cvp (p_agency TEXT, p_date TEXT) AS $$ BEGIN RAISE INFO 'Creating \'trips\' staging table';
-- Load vehicle trips into temporary table
DROP TABLE IF EXISTS staging__trips;
CREATE TEMP TABLE staging__trips AS
SELECT DISTINCT agency,
  "date",
  routename,
  direction,
  gtt_trip_id AS trip_instance_id,
  tripid
FROM ext_tsp.trips
WHERE agency = p_agency
  AND "date" = p_date;
RAISE INFO 'Creating \'vehicle_logs\' staging table';
-- Load vehicle logs into temporary table
DROP TABLE IF EXISTS staging__vehicle_logs;
CREATE TEMP TABLE staging__vehicle_logs AS WITH num_trips_per_trip_instance AS (
  SELECT trip_instance_id,
    COUNT(*)
  FROM staging__trips
  GROUP BY trip_instance_id
),
-- Ignore trip instances with multiple GTFS trips
invalid_trip_instances AS (
  SELECT trip_instance_id
  FROM num_trips_per_trip_instance
  WHERE "count" <> 1
)
SELECT vl.date AS trip_start_date,
  vl.timestamp,
  vl.lat AS latitude,
  vl.lon AS longitude,
  vl.speed,
  vl.agency AS agency_id,
  vl.gtt_trip_id AS trip_instance_id,
  -- Trip
  t.tripid AS trip_id,
  t.routename AS route_id,
  CASE
    t.direction
    WHEN 'outbound' THEN 0
    WHEN 'inbound' THEN 1
  END AS trip_direction_id,
  MIN(vl.timestamp) OVER (
    PARTITION BY vl.agency,
    vl.gtt_trip_id
  ) AS trip_start_time,
  'CVP' AS source_device
FROM ext_tsp.cvp_vehicle_logs vl
  LEFT JOIN invalid_trip_instances iti ON vl.gtt_trip_id = iti.trip_instance_id
  LEFT JOIN staging__trips t ON t.agency = vl.agency
  AND t.date = vl.date
  AND t.trip_instance_id = vl.gtt_trip_id
WHERE vl.agency = p_agency
  AND vl.date = p_date
  AND vl.event_type = 'GPS'
  AND iti.trip_instance_id IS NULL;
END;
$$ LANGUAGE plpgsql;