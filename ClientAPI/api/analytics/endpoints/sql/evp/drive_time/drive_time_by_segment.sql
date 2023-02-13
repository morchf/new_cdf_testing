-- drive_time_by_segment
WITH intersection_events AS (
  SELECT agency_id,
    trip_start_date,
    trip_start_time,
    intersection_id,
    "segment",
    MIN("timestamp") AS timestamp_start,
    MIN("timestamp") AS timestamp_end,
    AVG(speed) AS avg_speed,
    SUM(COALESCE("duration", 0)) AS drive_time,
    ANY_VALUE(intersection_start_id) AS intersection_start_id,
    ANY_VALUE(intersection_end_id) AS intersection_end_id
  FROM evp_events
  WHERE current_status = 'IN_TRANSIT_TO'
    AND trip_start_date BETWEEN '2022-06-01' AND '2022-06-30'
    AND intersection_start_id IS NOT NULL
    AND intersection_end_id IS NOT NULL
  GROUP BY agency_id,
    trip_start_date,
    trip_start_time,
    intersection_id,
    "segment"
)
SELECT intersection_start_id,
  intersection_end_id,
  COUNT(*) AS num_events,
  AVG(drive_time),
  MIN(drive_time),
  MAX(drive_time),
  SUM(drive_time),
  STDDEV(drive_time)
FROM intersection_events
GROUP BY intersection_start_id,
  intersection_end_id
ORDER BY num_events DESC,
  "avg" DESC