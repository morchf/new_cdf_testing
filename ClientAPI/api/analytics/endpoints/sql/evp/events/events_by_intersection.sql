-- events_by_intersection
WITH intersection_events_per_trip AS (
  SELECT DISTINCT trip_instance_id,
    segment,
    intersection_id
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-08-03'
),
events AS (
  SELECT COUNT(*) AS num_events,
    intersection_id
  FROM intersection_events_per_trip
  GROUP BY intersection_id
),
events_with_name AS (
SELECT
    num_events,
    intersection_id,
    "name"
FROM events
  LEFT JOIN evp.evp_intersections i ON intersection_id = location_id
WHERE intersection_id IS NOT NULL
ORDER BY 1 DESC
)
SELECT SUM(num_events)
FROM events_with_name