-- agg_lateness_per_route
WITH filtered AS (
  SELECT
    *,
    f_date_range_period(
      f_prior_date_range_start(%(start_date)s::DATE, %(end_date)s::DATE),
      %(start_date)s::DATE,
      stopstarttime::DATE
    ) AS "period",
    f_format_name(stopstart) AS stopstartname,
    f_format_name(stopend) AS stopendname
  FROM
    public.lateness_source_data
  WHERE
    agency = %(agency)s
    AND route = %(route)s
    AND "date" BETWEEN f_prior_date_range_start(
      %(start_date)s::DATE,
      %(end_date)s::DATE
    )
    AND %(end_date)s
    AND direction = ANY(%(selected_direction)s)
    AND {f_timeperiod} = ANY(%(selected_timeperiod)s)
),
per_period AS (
  SELECT
    -- Location
    stopstartname,
    stopstartid,
    stopendname,
    stopendid,
    direction,
    "period",
    ROUND(AVG(stopstartlatitude), 5) AS stopstartlatitude,
    ROUND(AVG(stopstartlongitude), 5) AS stopstartlongitude,
    ROUND(AVG(stopendlatitude), 5) AS stopendlatitude,
    ROUND(AVG(stopendlongitude), 5) AS stopendlongitude,
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
    stopstartname,
    stopstartid,
    stopendname,
    stopendid,
    direction,
    "period"
)
SELECT
	-- Location
	stopstartname,
  stopstartid,
	stopendname,
  stopendid,
	direction,
	"period",
	stopstartlatitude,
	stopstartlongitude,
	stopendlatitude,
	stopendlongitude,
	-- Schedule deviation
	{f_lag__start_lateness} AS stopstartlateness,
  {f_lag__end_lateness} AS stopendlateness,
  {f_lag__lateness_reduction} AS latenessreduction,
  -- On-time percentage
  {f_lag__early} AS earlypercentage,
  {f_lag__on_time} AS ontimepercentage,
  {f_lag__late} AS latepercentage
FROM
  per_period
ORDER BY
  stopstartname,
  stopendname,
  "period"