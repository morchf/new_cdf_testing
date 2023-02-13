-- speed_delta_by_intersection
WITH speed_delta_by_intersection_trip_instance AS (
SELECT
    trip_start_date,
    trip_instance_id,
    intersection_id,
    MAX(speed) - MIN(speed) AS speed_delta
FROM
    evp_events
WHERE intersection_id IS NOT NULL
GROUP BY
    trip_start_date,
    trip_instance_id,
    intersection_id
)
SELECT
    intersection_id,
    COUNT(DISTINCT trip_instance_id) AS num_events,
    AVG(speed_delta) AS avg_speed_delta,
    STDDEV(speed_delta) AS std_speed_delta,
    MAX(speed_delta) AS max_speed_delta,
    MIN(speed_delta) AS min_speed_delta
FROM speed_delta_by_intersection_trip_instance
GROUP BY intersection_id
ORDER BY avg_speed_delta DESC
