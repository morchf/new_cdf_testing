-- speed_delta_by_corridor
WITH speed_delta_by_intersection_trip_instance AS (
SELECT
    agency_id,
    trip_start_date,
    trip_instance_id,
    intersection_id,
    MAX(speed) - MIN(speed) AS speed_delta
FROM
    evp_events
WHERE intersection_id IS NOT NULL
GROUP BY
    agency_id,
    trip_start_date,
    trip_instance_id,
    intersection_id
),
speed_delta_with_corridor AS (
  SELECT t.*,
    ct.corridor_id,
    ct.corridor_name
  FROM speed_delta_by_intersection_trip_instance t
  LEFT OUTER JOIN mv_evp_corridor_trips ct USING (agency_id, trip_start_date, trip_instance_id)
)
SELECT
    corridor_id,
    corridor_name,
    COUNT(DISTINCT trip_instance_id) AS num_events,
    AVG(speed_delta) AS avg_speed_delta,
    STDDEV(speed_delta) AS std_speed_delta,
    MAX(speed_delta) AS max_speed_delta,
    MIN(speed_delta) AS min_speed_delta
FROM speed_delta_with_corridor
WHERE corridor_id IS NOT NULL
GROUP BY corridor_id, corridor_name
ORDER BY num_events DESC
LIMIT 10
