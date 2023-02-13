CREATE MATERIALIZED VIEW mv_intersection_dates AS WITH intersection_dates AS (
  SELECT
    DISTINCT agency_id,
    agency,
    "date"
  FROM
    mv_intersections
),
closest_date AS (
  SELECT
    ld.agency,
    ld.date,
    id.agency_id,
    id.date AS intersection_date,
    ROW_NUMBER() OVER (
      PARTITION BY ld.agency,
      ld.date
      ORDER BY
        id.date DESC
    ) = 1 AS is_closest_date
  FROM
    log_dates ld
    JOIN intersection_dates id ON ld.agency = id.agency
    AND ld.date >= id.date
)
SELECT
  DISTINCT agency_id,
  agency,
  "date",
  intersection_date
FROM
  closest_date
WHERE
  is_closest_date