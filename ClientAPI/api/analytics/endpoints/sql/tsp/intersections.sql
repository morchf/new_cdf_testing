-- route_intersections
SELECT
  route_id,
  "route",
  trip_direction_id,
  device_id,
  location_id,
  location_name,
  latitude,
  longitude
FROM
  mv_intersections
WHERE
  agency = %(agency)s
  AND "date" = %(date)s
  AND "route" = %(route)s
  AND trip_direction_id = ANY(%(direction_ids)s)