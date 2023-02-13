CREATE
OR REPLACE VIEW v_signal_delay AS
SELECT
  agency_id AS agency,
  trip_start_date AS DATE,
  trip_id || trip_start_time AS gtt_trip_id,
  location_id AS locationid,
  intersection_name AS locationname,
  route_id AS route,
  trip_direction_id,
  trip_start_time AS "timestamp",
  signal_delay AS signaldelay
FROM
  mv_signal_delay
WHERE
  intersection_id IS NOT NULL