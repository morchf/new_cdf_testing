CREATE
OR REPLACE PROCEDURE sp_intersections__routes (p_agency TEXT, p_date TEXT) AS $$ BEGIN
  RAISE INFO 'Creating \'intersections\' staging table';

-- Load intersections into temporary table
DROP TABLE IF EXISTS staging__intersections;

CREATE TEMP TABLE staging__intersections AS
SELECT
  route_short_name AS route_id,
  direction_id,
  latitude,
  longitude,
  agency,
  deviceid AS intersection_id
FROM
  mv_intersections
WHERE
  agency = p_agency
  AND "date" = (
    SELECT
      intersection_date
    FROM
      mv_intersection_dates
    WHERE
      agency = p_agency
      AND "date" = p_date
  );

END;

$$ LANGUAGE plpgsql;