-- routes_map_data
WITH routes AS (
  SELECT
    "date",
    route_id
  FROM
    gtfs.routes
  WHERE
    agency = 'sfmta'
    AND route_short_name = '22'
    AND "date" BETWEEN '2021-08-01'
    AND '2021-09-05'
),
trips AS (
  SELECT
    "date",
    route_id,
    trip_id,
    shape_id,
    direction_id_str AS direction
  FROM
    (
      SELECT
        "date",
        route_id,
        trip_id,
        shape_id,
        direction_id_str,
        ROW_NUMBER() OVER (
          PARTITION BY "date", route_id, shape_id
          ORDER BY
            lpad(trip_id, 15, '0') DESC
        ) AS desc_row_number
      FROM
        (
          SELECT
            CASE
              direction_id
              WHEN 0 THEN 'outbound'
              WHEN 1 THEN 'inbound'
            END AS direction_id_str,
            *
          FROM
            gtfs.trips
        )
      WHERE
        agency = 'sfmta'
        AND "date" BETWEEN '2021-08-01'
        AND '2021-09-05'
        AND "direction_id_str" = ANY(ARRAY['inbound'])
    )
  WHERE
    desc_row_number = 1
),
shapes AS (
  SELECT
    "date",
    shape_id,
    MIN(shape_pt_sequence),
    ST_LineFromMultiPoint(
      ST_Collect(point)
    ) AS line,
    JSON_PARSE('[' || listagg('["' || shape_pt_sequence || '","' || shape_pt_lat || '","' || shape_pt_lon || '"]', ',') || ']') AS points
  FROM
    (
      SELECT *,
        ST_POINT(shape_pt_lon, shape_pt_lat) AS point
      FROM gtfs.shapes
      ORDER BY shape_pt_sequence
    )
  WHERE
    agency = 'sfmta'
    AND "date" BETWEEN '2021-08-01'
    AND '2021-09-05'
  GROUP BY
    "date",
    shape_id
),
stop_times AS (
  SELECT
    "date",
    stop_id,
    stop_sequence,
    trip_id
  FROM
    gtfs.stop_times
  WHERE
    agency = 'sfmta'
    AND "date" BETWEEN '2021-08-01'
    AND '2021-09-05'
),
stops AS (
  SELECT
    "date",
    trip_id,
    JSON_PARSE('[' || listagg('["' || stop_sequence || '","' || stop_name || '","' || stop_lat || '","' || stop_lon || '","' || stop_id || '"]', ',') || ']') AS stops
  FROM
    stop_times
    JOIN gtfs.stops USING ("date", stop_id)
  GROUP BY
    "date",
    trip_id
)
SELECT
  "date",
  trip_id,
  shape_id,
  direction,
  line,
  points,
  stops
FROM
  routes
  JOIN trips USING ("date", route_id)
  JOIN shapes USING ("date", shape_id)
  JOIN stops USING ("date", trip_id)
ORDER BY
  "date" DESC,
  shape_id