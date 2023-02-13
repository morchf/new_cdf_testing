CREATE
OR REPLACE PROCEDURE sp_parse_vehicle_logs__mp70 (p_agency TEXT, p_utc_date TEXT) AS $$
DECLARE
  l_agency_id TEXT;

BEGIN
  RAISE INFO 'Parsing vehicle logs from MP70 data for agency=%, date=%',
  p_agency,
  p_utc_date;

SELECT
  INTO l_agency_id agency_id
FROM
  cfg_agency
WHERE
  agency = p_agency;

RAISE INFO 'Removing existing segment and intersection events';

-- Delete existing
DELETE FROM
  evp_events
WHERE
  agency_id = l_agency_id
  AND trip_start_date = p_utc_date;

-- Create 'vehicle_logs' and 'intersections' staging tables
CALL sp_vehicle_positions__mp70(l_agency_id, p_utc_date);

CALL sp_intersections__evp(l_agency_id, p_utc_date);

-- Create 'intersection_positions' staging table
CALL sp_intersection_positions__evp();

-- Create 'evp_events' staging table
CALL sp_evp_events();

RAISE INFO 'Copying \'evp_events\' staging table';

INSERT INTO
  evp_events
SELECT
  agency_id,
  trip_instance_id,
  "timestamp" :: TIMESTAMP,
  intersection_id,
  current_status,
  latitude,
  longitude,
  speed,
  trip_start_time,
  trip_start_date,
  -- Segment-based metrics
  "segment",
  intersection_start_id,
  intersection_end_id,
  "duration"
FROM
  staging__evp_events;

END;

$$ LANGUAGE plpgsql;