-- agg_lateness_per_route_day
WITH filtered AS (
  SELECT
    *,
    f_period(%(period)s::VARCHAR, stopstarttime::DATE::VARCHAR) AS "period"
  FROM
    public.lateness_source_data
  WHERE
    agency = %(agency)s
    AND route = %(route)s
    AND "date" BETWEEN %(start_date)s
    AND %(end_date)s
    AND direction = ANY(%(selected_direction)s)
    AND {f_timeperiod} = ANY(%(selected_timeperiod)s)
)
SELECT
  "period",
  -- Schedule deviation
  ROUND(AVG(stopstartlateness::FLOAT), 3) AS stopstartlateness,
  ROUND(AVG(stopendlateness::FLOAT), 3) AS stopendlateness,
  ROUND(AVG(latenessreduction::FLOAT), 3) AS latenessreduction,
  -- On-time percentage
  {f_percentage__early} AS earlypercentage,
  {f_percentage__on_time} AS ontimepercentage,
  {f_percentage__late} AS latepercentage
FROM
  filtered
GROUP BY
  "period"
ORDER BY
  "period"