CREATE
OR REPLACE PROCEDURE sp_refresh_tsp__rt_gtfs (p_agency TEXT) AS $$
DECLARE
  l_agency_id TEXT;

BEGIN
  SELECT
    INTO l_agency_id agency_id
  FROM
    cfg_agency
  WHERE
    agency = p_agency;

-- Refresh log dates
DELETE FROM
  log_dates
WHERE
  agency = p_agency;

INSERT INTO
  log_dates
SELECT
  DISTINCT p_agency AS agency,
  utc_date AS "date"
FROM
  ext_tsp.rt_gtfs_vehicle_positions
WHERE
  agency_id = l_agency_id;

-- Intersection locations
REFRESH MATERIALIZED VIEW mv_intersections;

REFRESH MATERIALIZED VIEW mv_intersection_dates;

-- Stop locations
REFRESH MATERIALIZED VIEW mv_gtfs_dates;

END;

$$ LANGUAGE plpgsql;