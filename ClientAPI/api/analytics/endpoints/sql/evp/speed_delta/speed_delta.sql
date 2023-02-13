-- speed_delta
WITH speed_delta_by_intersection_trip_instance AS (
SELECT
    trip_start_date,
    trip_instance_id,
    intersection_id,
    MAX(speed) - MIN(speed) AS speed_delta
FROM
    evp_events
WHERE intersection_id IS NOT NULL
--AND trip_start_date BETWEEN '2022-06-01' AND '2022-07-05'
AND trip_start_date BETWEEN '2022-07-06' AND '2022-08-03'
GROUP BY
    trip_start_date,
    trip_instance_id,
    intersection_id
)
SELECT
    AVG(speed_delta) AS avg_speed_delta,
    MIN(speed_delta) AS min_speed_delta,
    MAX(speed_delta) AS max_speed_delta,
    STDDEV(speed_delta) AS std_speed_delta
FROM speed_delta_by_intersection_trip_instance
ORDER BY avg_speed_delta DESC
