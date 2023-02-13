CREATE OR REPLACE PROCEDURE sp_refresh_travel_time ()
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW mv_availability;

  REFRESH MATERIALIZED VIEW mv_dwell_time;
  REFRESH MATERIALIZED VIEW mv_signal_delay;
  REFRESH MATERIALIZED VIEW mv_drive_time;

  REFRESH MATERIALIZED VIEW mv_travel_time;
END;
$$ LANGUAGE plpgsql;
