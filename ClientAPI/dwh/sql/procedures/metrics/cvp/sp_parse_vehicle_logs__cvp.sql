CREATE
OR REPLACE PROCEDURE sp_parse_vehicle_logs__cvp (p_agency TEXT, p_date TEXT) AS $$ BEGIN
  RAISE INFO 'Parsing vehicle logs from CVP data for agency=%, date=%',
  p_agency,
  p_date;

RAISE INFO 'Removing existing segment and intersection events';

-- Delete existing
DELETE FROM
  segment_events
WHERE
  agency_id = p_agency
  AND trip_start_date = p_date;

DELETE FROM
  intersection_events
WHERE
  agency_id = p_agency
  AND trip_start_date = p_date;

-- Create 'vehicle_logs' staging tables
CALL sp_vehicle_logs__cvp(p_agency, p_date);

-- Create 'vehicle_positions' staging table
CALL sp_vehicle_positions();

-- Create 'intersection_positions' staging table
CALL sp_intersection_positions();

-- Create 'segment_events' staging table
CALL sp_segment_events();

-- Create 'segment_events' staging table
RAISE INFO 'Copying \'intersection_events\' staging table';

-- Copy staging tables
INSERT INTO
  intersection_events
SELECT
  agency_id,
  trip_instance_id,
  "timestamp" :: TIMESTAMP,
  intersection_id,
  latitude,
  longitude,
  speed,
  trip_id,
  route_id,
  trip_direction_id,
  trip_start_time,
  trip_start_date,
  "segment",
  "duration"
FROM
  staging__segment_events
WHERE
  current_status = 'AT_INTERSECTION';

RAISE INFO 'Copying \'segment_events\' staging table';

INSERT INTO
  segment_events
SELECT
  agency_id,
  trip_instance_id,
  "timestamp" :: TIMESTAMP,
  stop_id,
  CASE
    WHEN current_status = 'AT_INTERSECTION' THEN 'IN_TRANSIT_TO'
    ELSE current_status
  END AS current_status,
  NULL AS current_stop_sequence,
  NULL AS congestion_level,
  NULL AS occupancy_status,
  NULL AS vehicle_id,
  NULL AS vehicle_label,
  NULL AS license_plate,
  latitude,
  longitude,
  speed,
  NULL AS odometer,
  NULL AS bearing,
  trip_id,
  route_id,
  trip_direction_id,
  trip_start_time,
  trip_start_date,
  "segment",
  stop_start_id,
  stop_end_id,
  "duration",
  'CVP' AS source_device
FROM
  staging__segment_events;

END;

$$ LANGUAGE plpgsql;