CREATE MATERIALIZED VIEW mv_gtfs_stops AS WITH gtfs_trip_stops AS (
  SELECT
    DISTINCT agency,
    date,
    trip_id,
    stop_id,
    stop_sequence
  FROM
    gtfs.stop_times
),
gtfs_trips AS (
  SELECT
    DISTINCT agency,
    date,
    route_id,
    direction_id,
    trip_id
  FROM
    gtfs.trips
),
gtfs_stops_order AS (
  SELECT
    DISTINCT t.route_id,
    t.direction_id,
    ts.agency,
    ts.date,
    ts.stop_id,
    ts.stop_sequence,
    t.trip_id,
    ROW_NUMBER() OVER (
      PARTITION BY ts.agency,
      ts.date,
      t.route_id,
      t.trip_id,
      ts.stop_id
      ORDER BY
        ts.stop_sequence
    ) AS repeat_stop_order
  FROM
    gtfs_trip_stops ts
    LEFT JOIN gtfs_trips t ON t.agency = ts.agency
    AND t.date = ts.date
    AND t.trip_id = ts.trip_id
),
gtfs_routes AS (
  SELECT
    DISTINCT agency,
    "date",
    route_id,
    route_short_name,
    route_long_name
  FROM
    gtfs.routes
),
gtfs_stops AS (
  SELECT
    agency,
    "date",
    stop_id,
    TRIM(stop_name) AS stop_name,
    stop_lat,
    stop_lon
  FROM
    gtfs.stops
)
SELECT
  *,
  MAX(repeat_stop_order) OVER (
    PARTITION BY agency,
    "date",
    trip_id,
    stop_id
  ) - 1 AS num_repeats
FROM
  gtfs_stops s
  JOIN gtfs_stops_order USING (agency, "date", stop_id)