-- signal_delay
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
--AND trip_start_date BETWEEN '2022-06-01' AND '2022-07-05'
AND trip_start_date BETWEEN '2022-07-06' AND '2022-08-03'
  GROUP BY agency_id,
    trip_start_date,
    trip_start_time,
    intersection_id,
    "segment"
)
SELECT
    COUNT(*) AS num_events,
    SUM((signal_delay > 30)::INT)::FLOAT / num_events AS perc_high_impact,
    AVG(signal_delay) AS avg_signal_delay,
    MIN(signal_delay) AS min_signal_delay,
    MAX(signal_delay) AS max_signal_delay,
    STDDEV(signal_delay) AS std_signal_delay
FROM intersection_events