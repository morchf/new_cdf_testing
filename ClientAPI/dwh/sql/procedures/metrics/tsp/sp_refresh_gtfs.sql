CREATE OR REPLACE PROCEDURE sp_refresh_gtfs ()
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW mv_gtfs_stops;
  REFRESH MATERIALIZED VIEW mv_gtfs_segments;
END;
$$ LANGUAGE plpgsql;
