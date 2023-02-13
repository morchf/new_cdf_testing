CREATE
OR REPLACE PROCEDURE sp_intersection_positions__evp () AS $$ BEGIN
  RAISE INFO 'Creating \'intersection_positions\' staging table';

DROP TABLE IF EXISTS staging__intersection_positions;

CREATE TEMP TABLE staging__intersection_positions AS WITH insersection_events AS (
  SELECT
    vp. *,
    -- Get closest intersection for each GPS point
    i.intersection_id,
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
    staging__vehicle_positions vp -- Find closest intersection location date
    LEFT JOIN staging__intersections i ON ST_DistanceSphere(
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