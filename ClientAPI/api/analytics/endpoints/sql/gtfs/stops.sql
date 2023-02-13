SELECT
  *
FROM
  gtfs.mv_routes_map_data
WHERE
  agency = %(agency)s
  AND route = %(route)s
  AND "date" BETWEEN %(start_date)s
  AND %(end_date)s
  AND direction_id = ANY(%(direction_ids)s)
ORDER BY
  "date" DESC,
  route,
  shape_id