CREATE MATERIALIZED VIEW mv_signal_delay AS WITH signal_delay AS (
  SELECT agency_id,
    trip_instance_id,
    "segment",
    intersection_id,
    ANY_VALUE(trip_start_date) AS trip_start_date,
    ANY_VALUE(trip_start_time) AS trip_start_time,
    ANY_VALUE(trip_id) AS trip_id,
    ANY_VALUE(route_id) AS route_id,
    ANY_VALUE(trip_direction_id) AS trip_direction_id,
    AVG(speed) AS avg_speed,
    MIN("timestamp") AS timestamp_start,
    SUM(COALESCE("duration", 0)) AS signal_delay
  FROM intersection_events
  GROUP BY agency_id,
    trip_instance_id,
    "segment",
    intersection_id
)
SELECT DISTINCT sd.*,
  id.intersection_date,
  i.device_id,
  i.location_id,
  i.location_name AS intersection_name
FROM signal_delay sd
  LEFT JOIN mv_intersection_dates id ON sd.agency_id = id.agency
  AND sd.trip_start_date = id.date
  LEFT JOIN mv_intersections i ON i.agency = sd.agency_id
  AND i.date = id.intersection_date
  AND i.route = sd.route_id
  AND (
    i.location_id = sd.intersection_id
    OR i.device_id = sd.intersection_id
  )