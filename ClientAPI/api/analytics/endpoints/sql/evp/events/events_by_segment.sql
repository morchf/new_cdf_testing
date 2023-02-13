-- segments
WITH trips AS (
  SELECT trip_start_date,
    trip_instance_id,
    intersection_start_id,
    intersection_end_id,
    SUM(DURATION) AS segment_duration
  FROM evp_events
  WHERE trip_start_date BETWEEN '2022-06-01' AND '2022-06-30'
    AND (
      intersection_start_id IS NOT NULL
      OR intersection_end_id IS NOT NULL
    )
  GROUP BY trip_start_date,
    trip_instance_id,
    intersection_start_id,
    intersection_end_id
)
SELECT intersection_start_id,
  intersection_end_id,
  COUNT(*) AS num_events,
  AVG(segment_duration),
  MIN(segment_duration),
  MAX(segment_duration),
  SUM(segment_duration),
  STDDEV(segment_duration)
FROM trips
WHERE intersection_start_id IS NOT NULL
  AND intersection_end_id IS NOT NULL
GROUP BY intersection_start_id,
  intersection_end_id
ORDER BY num_events DESC,
  "avg" DESC
