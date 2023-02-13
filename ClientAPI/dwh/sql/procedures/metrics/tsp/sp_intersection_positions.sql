CREATE
OR REPLACE PROCEDURE sp_intersection_positions () AS $$ BEGIN
  DROP TABLE IF EXISTS staging__intersection_positions;

RAISE INFO 'Creating \'intersection_positions\' staging table';

CREATE TEMP TABLE staging__intersection_positions AS WITH insersection_events AS (
  SELECT
    vp. *,
    -- Get closest stop for each GPS point
    i.location_id AS intersection_id,
    ST_DistanceSphere(
      ST_Point(vp.longitude :: FLOAT, vp.latitude :: FLOAT),
      ST_Point(
        i.longitude :: FLOAT,
        i.latitude :: FLOAT
      )
    ) AS intersection_distance,
    ROW_NUMBER() OVER (
      PARTITION BY trip_instance_id,
      "timestamp"
      ORDER BY
        intersection_distance
    ) = 1 AS is_closest_intersection
  FROM
    staging__vehicle_positions vp
    LEFT JOIN mv_intersection_dates id ON vp.agency_id = id.agency
    AND vp.trip_start_date = id.date
    LEFT OUTER JOIN mv_intersections i ON i.agency = vp.agency_id
    AND i.date = id.intersection_date
    AND i.route = vp.route_id
    AND i.trip_direction_id = vp.trip_direction_id
    /* Map GPS coordinates to closest intersection (within 30 meters) */
    AND ST_DistanceSphere(
      ST_Point(vp.longitude :: FLOAT, vp.latitude :: FLOAT),
      ST_Point(
        i.longitude :: FLOAT,
        i.latitude :: FLOAT
      )
    ) < 30.0
)
SELECT
  *
FROM
  insersection_events
WHERE
  -- Select closest intersection to GPS events
  is_closest_intersection;

END;

$$ LANGUAGE plpgsql;