CREATE MATERIALIZED VIEW gtfs.mv_routes_map_data AUTO REFRESH YES
/**
 * Aggregate unique trip shapes
 */
AS WITH routes AS (
  SELECT
    agency,
    "date",
    route_id,
    route_short_name AS route
  FROM
    gtfs.routes
),
trips AS (
  SELECT
    agency,
    "date",
    route_id,
    trip_id,
    shape_id,
    direction_id
  FROM
    (
      SELECT
        *,
        ROW_NUMBER() OVER (
          PARTITION BY agency,
          "date",
          route_id,
          shape_id
          ORDER BY
            lpad(trip_id, 15, '0') DESC
        ) AS desc_row_number
      FROM
        gtfs.trips
    )
  WHERE
    desc_row_number = 1
),
shapes AS (
  SELECT
    agency,
    "date",
    shape_id,
    ST_LineFromMultiPoint(
      ST_Collect(ST_POINT(shape_pt_lon, shape_pt_lat)) WITHIN GROUP (
        ORDER BY
          shape_pt_sequence
      )
    ) AS line
  FROM
    gtfs.shapes
  GROUP BY
    agency,
    "date",
    shape_id
),
stop_times AS (
  SELECT
    agency,
    "date",
    stop_id,
    stop_sequence,
    trip_id
  FROM
    gtfs.stop_times
),
stops AS (
  SELECT
    agency,
    "date",
    trip_id,
    JSON_PARSE(
      '[' || listagg(
        '["' || stop_sequence || '","' || stop_name || '","' || stop_lat || '","' || stop_lon || '","' || stop_id || '"]',
        ','
      ) || ']'
    ) AS stops
  FROM
    stop_times
    JOIN gtfs.stops USING (agency, "date", stop_id)
  GROUP BY
    agency,
    "date",
    trip_id
)
SELECT
  agency,
  route,
  route_id,
  "date",
  trip_id,
  shape_id,
  direction_id,
  line,
  stops
FROM
  routes
  JOIN trips USING (agency, "date", route_id)
  JOIN shapes USING (agency, "date", shape_id)
  JOIN stops USING (agency, "date", trip_id);