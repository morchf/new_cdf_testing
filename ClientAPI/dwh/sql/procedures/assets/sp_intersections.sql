CREATE
OR REPLACE PROCEDURE assets.sp_intersections (p_agency_id TEXT, p_utc_date TEXT) AS $$
DECLARE
  l_agency TEXT;

l_gtfs_date TEXT;

BEGIN
  -- Map params to 'agency' and statc GTFS date */
  SELECT
    INTO l_agency agency
  FROM
    cfg_agency
  WHERE
    agency_id = p_agency_id;

SELECT
  INTO l_gtfs_date MAX(gd.date)
FROM
  gtfs.agency gd
WHERE
  gd.agency = l_agency
  AND gd.date <= p_utc_date;

DROP TABLE IF EXISTS staging__intersections;

CREATE TEMPORARY TABLE staging__intersections AS WITH intersections AS (
  SELECT
    *,
    l_agency AS agency,
    signal_location AS location_id
  FROM
    ext_analytics.ast_intersections l (
      fid,
      i_oid,
      signal_location,
      "owner",
      "municipality",
      "county",
      brt_line,
      tsp_type,
      tsp_status,
      comm_type,
      controller_type,
      existing_miovision_equipment,
      gtt_equipment_needed,
      signal_installation,
      miovision_equipment,
      miovision_comms,
      signal_installs
    )
  WHERE
    agency_id = p_agency_id
    AND utc_date = p_utc_date
)
SELECT
  i. *,
  l.longitude :: FLOAT AS longitude,
  l.latitude :: FLOAT AS latitude,
  l.address AS street_address
FROM
  intersections i
  JOIN ext_analytics.ast_locations l ON i.agency_id = l.agency_id
  AND i.utc_date = l.utc_date
  AND i.signal_location = l.street
-- Only accept properly formatted coordinates
WHERE longitude ~ '^\-?\\d+.\\d+$'
AND latitude ~'^\-?\\d+.\\d+$';

-- Map intersections to routes
DROP TABLE IF EXISTS staging__route_intersections;

CREATE TEMPORARY TABLE staging__route_intersections AS
SELECT
  i. *,
  rmd.route,
  rmd.route_id,
  rmd.direction_id :: INT AS trip_direction_id,
  ST_LineFromMultiPoint(ST_Points(ST_Point(i.longitude, i.latitude))) AS "point",
  rmd.line,
  f_euclidean_geodistance("point", rmd.line) AS route_distance
FROM
  staging__intersections i
  CROSS JOIN gtfs.mv_routes_map_data rmd
WHERE
  rmd.agency = i.agency
  AND rmd.date = l_gtfs_date
  AND route_distance < 30;

-- Remove existing
DELETE FROM
  assets.intersections
WHERE
  agency_id = p_agency_id
  AND utc_date = p_utc_date;

-- Insert transformed
INSERT INTO
  assets.intersections
SELECT
  route_id,
  "route",
  trip_direction_id,
  NULL AS device_id,
  location_id,
  street_address,
  latitude,
  longitude,
  -1 :: INT AS "sequence",
  agency,
  agency_id,
  utc_date
FROM
  staging__route_intersections i;

END;

$$ LANGUAGE plpgsql;