CREATE MATERIALIZED VIEW mv_availability AUTO REFRESH YES AS WITH schedule_deviation AS (
  SELECT
    DISTINCT agency,
    "date" AS sd_date
  FROM
    lateness_source_data
),
travel_time AS (
  SELECT
    DISTINCT agency_id AS agency,
    trip_start_date AS tt_date
  FROM
    segment_events
)
SELECT
  agency,
  MIN(sd_date) AS schedule_deviation_min,
  MAX(sd_date) AS schedule_deviation_max,
  MIN(tt_date) AS travel_time_min,
  MAX(tt_date) AS travel_time_max
FROM
  schedule_deviation sd FULL
  OUTER JOIN travel_time tt USING (agency)
WHERE
  agency IS NOT NULL
GROUP BY
  agency