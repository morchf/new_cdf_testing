-- trips__simple
WITH trips AS (
  SELECT agency_id,
    trip_instance_id,
    trip_start_date,
    MAX("timestamp") - MIN("timestamp") AS trip_duration
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-08-03'
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
  AVG(trip_duration) AS avg_trip_duration
FROM trips_with_corridors
WHERE corridor_id IS NOT NULL
GROUP BY agency_id,
  corridor_id,
  corridor_name
ORDER BY num_trips DESC
LIMIT 10