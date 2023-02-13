-- agg_lateness_reduction
WITH filtered AS (
  SELECT
    route,
    stopendlateness::FLOAT AS stopendlateness
  FROM
    public.lateness_source_data
  WHERE
    agency = %(agency)s
    AND "date" BETWEEN %(start_date)s
    AND %(end_date)s
    AND direction = ANY(%(selected_direction)s)
    AND {f_timeperiod} = ANY(%(selected_timeperiod)s)
)
SELECT
  route,
  ROUND(AVG(stopendlateness), 3) AS avgscheduledeviation,
  {f_percentage__early} AS earlypercentage,
  {f_percentage__on_time} AS ontimepercentage,
  {f_percentage__late} AS latepercentage
FROM
  filtered
GROUP BY
  route