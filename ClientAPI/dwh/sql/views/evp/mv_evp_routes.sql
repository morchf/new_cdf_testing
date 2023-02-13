CREATE MATERIALIZED VIEW mv_evp_routes AS WITH raw_intersections AS (
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
),
intersections AS (
  SELECT
    agency_id,
    utc_date,
    intersection_id,
    intersection_number
  FROM
    raw_intersections
)
SELECT
  i1.agency_id,
  i1.utc_date,
  i1.intersection_id AS intersection_start_id,
  i2.intersection_id AS intersection_end_id,
  i1.intersection_id || ' / ' || i2.intersection_id AS route_id
FROM
  intersections i1
  JOIN intersections i2 USING (agency_id, utc_date)