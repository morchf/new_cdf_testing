-- intersection_speed
WITH speed_per_trip AS (
  SELECT AVG(speed) AS avg_kph
  FROM evp_events
--  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-07-05'
  WHERE trip_start_date BETWEEN '2022-07-06' AND '2022-08-03'
  AND current_status = 'AT_INTERSECTION'
  GROUP BY trip_start_date,
    trip_instance_id
)
SELECT
    AVG(avg_kph) AS avg_kph,
    MAX(avg_kph) AS max_avg_kph,
    MIN(avg_kph) AS min_avg_kph,
    STDDEV(avg_kph) AS std_avg_kph
FROM speed_per_trip
