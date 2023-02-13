CREATE MATERIALIZED VIEW mv_evp_dates AS WITH intersection_dates AS (
  SELECT DISTINCT agency_id,
    utc_date
  FROM ext_evp.intersections
),
dates AS (
  SELECT DISTINCT utcdate AS utc_date
  FROM ext_analytics.mp70
),
closest_date AS (
  SELECT id.agency_id,
    dates.utc_date,
    id.utc_date AS intersection_utc_date,
    ROW_NUMBER() OVER (
      PARTITION BY dates.utc_date
      ORDER BY dates.utc_date DESC
    ) = 1 AS is_closest_date
  FROM dates
    JOIN intersection_dates id ON dates.utc_date >= id.utc_date
)
SELECT DISTINCT agency_id,
  utc_date,
  intersection_utc_date AS device_utc_date
FROM closest_date
WHERE is_closest_date