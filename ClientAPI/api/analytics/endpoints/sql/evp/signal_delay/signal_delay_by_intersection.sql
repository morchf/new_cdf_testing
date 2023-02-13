-- signal_delay_by_intersection
WITH intersection_events AS (
  SELECT agency_id,
    trip_start_date,
    trip_start_time,
    intersection_id,
    "segment",
    MIN("timestamp") AS timestamp_start,
    MIN("timestamp") AS timestamp_end,
    AVG(speed) AS avg_speed,
    SUM(COALESCE("duration", 0)) AS signal_delay
  FROM evp_events
  WHERE current_status = 'AT_INTERSECTION'
    AND trip_start_date BETWEEN '2022-06-01' AND '2022-06-30'
  GROUP BY agency_id,
    trip_start_date,
    trip_start_time,
    intersection_id,
    "segment"
),
metrics AS (
  SELECT intersection_id,
    COUNT(*) AS num_events,
    SUM((signal_delay > 30)::INT)::FLOAT / num_events AS perc_high_impact,
    AVG(signal_delay),
    SUM(signal_delay),
    MIN(signal_delay),
    MAX(signal_delay),
    STDDEV(signal_delay)
  FROM intersection_events
  GROUP BY intersection_id
)
SELECT *
FROM metrics
ORDER BY num_events DESC