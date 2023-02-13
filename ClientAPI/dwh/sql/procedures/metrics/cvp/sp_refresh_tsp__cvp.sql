CREATE OR REPLACE PROCEDURE sp_refresh_tsp__cvp (p_agency text)
  AS $$
BEGIN
  -- Refresh log dates
  DELETE FROM log_dates
  WHERE agency = p_agency;
  INSERT INTO log_dates SELECT DISTINCT
    agency,
    "date"
  FROM
    ext_tsp.cvp_vehicle_logs
  WHERE
    agency = p_agency;
  -- Intersection locations
  REFRESH MATERIALIZED VIEW mv_intersections;
  REFRESH MATERIALIZED VIEW mv_intersection_dates;
  REFRESH MATERIALIZED VIEW mv_intersections;
  -- Stop locations
  REFRESH MATERIALIZED VIEW mv_gtfs_dates;
END;
$$
LANGUAGE plpgsql;

