CREATE MATERIALIZED VIEW mv_gtfs_dates AS WITH gtfs_dates AS (
  SELECT
    DISTINCT agency,
    "date"
  FROM
    gtfs.agency
),
closest_date AS (
  SELECT
    ld.agency,
    ld.date,
    gd.date AS gtfs_date,
    ROW_NUMBER() OVER (
      PARTITION BY ld.agency,
      ld.date
      ORDER BY
        gd.date DESC
    ) = 1 AS is_closest_date
  FROM
    log_dates ld
    JOIN gtfs_dates gd ON ld.agency = gd.agency
    AND ld.date >= gd.date
)
SELECT
  DISTINCT agency,
  "date",
  gtfs_date
FROM
  closest_date
WHERE
  is_closest_date