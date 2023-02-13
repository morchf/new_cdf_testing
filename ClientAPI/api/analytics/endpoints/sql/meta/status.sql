SELECT schedule_deviation_min,
  schedule_deviation_max,
  travel_time_min,
  travel_time_max
FROM mv_availability
WHERE agency = %(agency)s
