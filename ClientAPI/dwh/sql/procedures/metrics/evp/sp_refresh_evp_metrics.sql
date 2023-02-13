CREATE
OR REPLACE PROCEDURE sp_refresh_evp_metrics() AS $$ BEGIN
  RAISE INFO 'Refreshing metrics';

END;

$$ LANGUAGE plpgsql;