SELECT
  MAX("date") AS "date"
FROM mv_intersections
WHERE
  agency = %(agency)s
  AND "route" = %(route)s
  AND trip_direction_id = ANY(%(direction_ids)s)
