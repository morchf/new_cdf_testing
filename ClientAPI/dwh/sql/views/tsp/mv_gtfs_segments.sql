CREATE MATERIALIZED VIEW mv_gtfs_segments AS
SELECT
  agency AS agency_id,
  "date",
  trip_id,
  stop_id AS stop_start_id,
  LEAD(stop_id) OVER (
    PARTITION BY agency,
    "date",
    trip_id
    ORDER BY
      stop_sequence
  ) AS stop_end_id
FROM
  mv_gtfs_stops