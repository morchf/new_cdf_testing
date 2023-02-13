CREATE
OR REPLACE PROCEDURE sp_refresh_tables__evp (p_agency TEXT, p_agency_id TEXT) AS $$ BEGIN

REFRESH MATERIALIZED VIEW mv_evp_dates;
REFRESH MATERIALIZED VIEW mv_evp_corridors;
REFRESH MATERIALIZED VIEW mv_evp_corridor_trips;

END;

$$ LANGUAGE plpgsql;