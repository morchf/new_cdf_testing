CREATE
OR REPLACE PROCEDURE sp_vehicle_positions () AS $$ BEGIN
  DROP TABLE IF EXISTS staging__vehicle_positions;

RAISE INFO 'Creating \'vehicle_positions\' staging table';

CREATE TEMP TABLE staging__vehicle_positions AS WITH gps_stops AS (
  SELECT
    vl. *,
    -- Stops
    stops.stop_id,
    stops.num_repeats,
    ST_DistanceSphere(
      ST_Point(vl.longitude :: FLOAT, vl.latitude :: FLOAT),
      ST_Point(stops.stop_lon :: FLOAT, stops.stop_lat :: FLOAT)
    ) AS stop_distance,
    -- Get closest stop for each GPS point
    ROW_NUMBER() OVER (
      PARTITION BY vl.agency_id,
      vl.trip_start_date,
      trip_instance_id,
      "timestamp"
      ORDER BY
        stop_distance
    ) = 1 AS is_closest_stop
  FROM
    staging__vehicle_logs vl
    LEFT JOIN mv_gtfs_dates gd ON vl.agency_id = gd.agency
    AND vl.trip_start_date = gd.date
    LEFT OUTER JOIN mv_gtfs_stops stops ON stops.agency = vl.agency_id
    AND stops.date = gd.gtfs_date
    AND stops.trip_id = vl.trip_id
    AND ST_DistanceSphere(
      ST_Point(vl.longitude :: FLOAT, vl.latitude :: FLOAT),
      ST_Point(stops.stop_lon :: FLOAT, stops.stop_lat :: FLOAT)
    ) < 500 -- Ignore any potential stop matches greater than 500 meters away
),
segment_start_events AS (
  SELECT
    *,
    COALESCE(
      LAG(stop_id) OVER (
        PARTITION BY trip_instance_id
        ORDER BY
          "timestamp"
      ),
      ''
    ) <> stop_id AS is_segment_start
  FROM
    gps_stops
  WHERE
    -- Select closest stop to GPS event
    is_closest_stop
),
segments AS (
  SELECT
    *,
    -- Continuous segments
    SUM((is_segment_start) :: INT) OVER (
      PARTITION BY trip_instance_id
      ORDER BY
        "timestamp" ROWS UNBOUNDED PRECEDING
    ) AS "segment"
  FROM
    segment_start_events
),
closest_per_segment AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY trip_instance_id,
      "segment"
      ORDER BY
        stop_distance
    ) = 1 AS is_closest_stop_in_segment,
    COUNT(*) OVER (PARTITION BY trip_instance_id, "segment") AS segment_length
  FROM
    segments
)
SELECT
  agency_id,
  trip_instance_id,
  /*
   VehiclePosition
   */
  "timestamp",
  -- Select all stop events, including 0-length events
  -- Order by closest event per-segment, preferring longer segments
  ROW_NUMBER() OVER (
    PARTITION BY trip_instance_id,
    stop_id
    ORDER BY
      is_closest_stop_in_segment DESC,
      segment_length DESC
  ) <= (num_repeats + 1) AS is_closest,
  CASE
    WHEN is_closest THEN stop_id
    WHEN stop_distance < 15.0 THEN stop_id
    ELSE NULL
  END AS stop_id,
  stop_distance,
  -- Position
  latitude,
  longitude,
  speed,
  -- TripDescriptor
  trip_id,
  route_id,
  trip_start_date,
  trip_start_time,
  trip_direction_id,
  -- Extra
  source_device
FROM
  closest_per_segment;

END;

$$ LANGUAGE plpgsql;