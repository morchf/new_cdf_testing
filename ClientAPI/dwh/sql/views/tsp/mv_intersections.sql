CREATE MATERIALIZED VIEW mv_intersections AS
SELECT
  DISTINCT agency,
  agency_id,
  "date",
  route_id,
  "route",
  trip_direction_id,
  device_id,
  location_id,
  location_name,
  latitude,
  longitude
FROM
  (
    SELECT
      rti.route_id,
      rti.route_short_name AS "route",
      rti.direction_id AS trip_direction_id,
      rti.deviceid AS device_id,
      rti.latitude::DOUBLE PRECISION AS latitude,
      rti.longitude::DOUBLE PRECISION AS longitude,
      rti.sequence,
      rti.agency,
      rti.agency AS agency_id,
      rti.date,
      isr.locationid AS location_id,
      isr.locationname AS location_name
    FROM
      route_to_intersection_mapping rti
      JOIN intersection_status_report isr USING (agency, "date", deviceid)
  )
UNION
SELECT
  DISTINCT agency,
  agency_id,
  "date",
  route_id,
  "route",
  trip_direction_id,
  device_id,
  location_id,
  location_name,
  latitude,
  longitude
FROM
  (
    SELECT
      DISTINCT agency,
      agency_id,
      utc_date AS "date",
      route_id,
      "route",
      trip_direction_id,
      NULL AS device_id,
      location_id,
      location_id AS location_name,
      latitude::DOUBLE PRECISION AS latitude,
      longitude ::DOUBLE PRECISION AS longitude
    FROM
      assets.intersections
  )