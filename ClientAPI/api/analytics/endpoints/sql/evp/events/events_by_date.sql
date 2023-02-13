-- events_by_date
WITH events AS (
  SELECT COUNT(DISTINCT segment) - 1 AS num_intersection_events,
    trip_start_date
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-06-30'
  GROUP BY trip_start_date,
    trip_instance_id
)
SELECT SUM(num_intersection_events) AS num_intersection_events,
  AVG(num_intersection_events) AS avg_num_intersection_events,
  STDDEV(num_intersection_events) AS std_num_intersection_events,
  MAX(num_intersection_events) AS num_intersection_events,
  trip_start_date
FROM events
GROUP BY trip_start_date
ORDER BY 1 DESC