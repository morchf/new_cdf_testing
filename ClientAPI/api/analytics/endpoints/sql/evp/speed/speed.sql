-- speed
WITH speed_per_trip AS (
  SELECT AVG(speed) AS avg_kph
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-07-01' AND '2022-07-20'
  GROUP BY trip_start_date,
    trip_instance_id
)
SELECT
    AVG(avg_kph)
FROM speed_per_trip

