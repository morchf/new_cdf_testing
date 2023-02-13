CREATE MATERIALIZED VIEW mv_evp_corridors AS WITH intersections AS (
  SELECT c.corridor_id,
    c.corridor_name,
    c.agency_id,
    c.utc_date,
    c.sequence,
    i.name,
    i.location_id
  FROM evp.evp_corridors c
    JOIN evp.evp_intersections i USING (agency_id, utc_date, location_id)
)
SELECT corridor_id,
  corridor_name,
  agency_id,
  utc_date,
  LISTAGG(location_id, ',') WITHIN GROUP (
    ORDER BY "sequence"
  ) AS location_ids
FROM intersections
GROUP BY corridor_id,
  corridor_name,
  agency_id,
  utc_date