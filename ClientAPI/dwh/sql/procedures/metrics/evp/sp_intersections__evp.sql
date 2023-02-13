CREATE
OR REPLACE PROCEDURE sp_intersections__evp (p_agency_id TEXT, p_utc_date TEXT) AS $$ BEGIN
  RAISE INFO 'Creating \'intersections\' staging table';

DROP TABLE IF EXISTS staging__intersections;

-- Load vehicle logs into temporary table
CREATE TEMP TABLE staging__intersections AS WITH params AS (
  SELECT
    device_utc_date
  FROM
    mv_evp_dates
  WHERE
    agency_id = p_agency_id
    AND utc_date = p_utc_date
)
SELECT
  *
FROM
  ext_evp.intersections AS i (
    "name",
    intersection_id,
    latitude,
    longitude,
    cabinet,
    controller,
    intersection_number,
    controlelr_lan_ip,
    make,
    model,
    signal_core_serial_number,
    "764_serial_number",
    lan_ip,
    miovision_ID,
    "764_configured",
    approach_threshold_adjusted,
    notes
  )
WHERE
  agency_id = p_agency_id
  AND utc_date = (
    SELECT
      device_utc_date
    FROM
      params
  );

END;

$$ LANGUAGE plpgsql;