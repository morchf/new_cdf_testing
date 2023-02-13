-- trips_by_date
WITH trips AS (
  SELECT trip_instance_id,
    trip_start_date,
    COUNT(*) AS num_logs,
    MAX("timestamp") - MIN("timestamp") AS trip_duration,
    SUM(
      (
        (intersection_start_id IS NOT NULL)
        OR (intersection_end_id IS NOT NULL)
      )::INT
    ) = 0 AS no_intersections
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-06-30'
  GROUP BY trip_instance_id,
    trip_start_date
)
SELECT trip_start_date,
  COUNT(*) AS num_trips,
  AVG(trip_duration) AS avg_trip_duration,
  MAX(trip_duration) AS max_trip_duration,
  MIN(trip_duration) AS min_trip_duration,
  SUM((no_intersections = TRUE)::INT) AS num_no_intersections,
  SUM((no_intersections = FALSE)::INT) AS num_intersections
FROM trips
GROUP BY trip_start_date
ORDER BY trip_start_date