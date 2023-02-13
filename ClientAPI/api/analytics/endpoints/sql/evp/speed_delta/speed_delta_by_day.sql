-- speed_delta_by_day
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
SELECT trip_start_date, AVG(speed_delta)
FROM speed_delta_by_intersection_trip_instance
GROUP BY trip_start_date
ORDER BY trip_start_date DESC