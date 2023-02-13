-- intersection_speed_by_intersection
WITH speed_per_intersection_event AS (
  SELECT AVG(speed) AS avg_kph,
    intersection_id
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-06-30'
  GROUP BY trip_start_date,
    trip_instance_id,
    segment,
    intersection_id
)
SELECT AVG(avg_kph) AS avg_kph_per_intersection,
  intersection_id
FROM speed_per_intersection_event
GROUP BY intersection_id
ORDER BY 1 DESC