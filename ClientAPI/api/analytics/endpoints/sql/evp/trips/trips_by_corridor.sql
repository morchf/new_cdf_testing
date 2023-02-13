-- trips_by_corridor
WITH trips AS (
  SELECT agency_id,
    trip_instance_id,
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
  GROUP BY agency_id,
    trip_instance_id,
    trip_start_date
),
trips_with_corridors AS (
  SELECT t.*,
    ct.corridor_id,
    ct.corridor_name
  FROM trips t
    LEFT OUTER JOIN mv_evp_corridor_trips ct USING (agency_id, trip_start_date, trip_instance_id)
)
SELECT corridor_id,
  corridor_name,
  COUNT(*) AS num_trips,
  AVG(trip_duration) AS avg_trip_duration,
  MAX(trip_duration) AS max_trip_duration,
  MIN(trip_duration) AS min_trip_duration,
  SUM((no_intersections = TRUE)::INT) AS num_trips_with_no_intersections,
  SUM((no_intersections = FALSE)::INT) AS num_trips_intersections
FROM trips_with_corridors
WHERE corridor_id IS NOT NULL
GROUP BY agency_id,
  corridor_id,
  corridor_name
ORDER BY num_trips DESC