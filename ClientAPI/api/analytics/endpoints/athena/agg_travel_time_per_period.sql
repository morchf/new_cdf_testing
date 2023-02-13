-- agg_travel_time_per_period
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
    public.mv_travel_time
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
trip_level AS (
  SELECT
    gtt_trip_id,
    "period",
    SUM(drivetime::FLOAT) AS drivetime,
    SUM(dwelltime::FLOAT) AS dwelltime,
    SUM(signaldelay::FLOAT) AS signaldelay,
    SUM(tspsavings::FLOAT) AS tspsavings
  FROM
    filtered
  GROUP BY
    gtt_trip_id,
    "period"
),
agg_travel_time AS (
  SELECT
    COUNT(DISTINCT gtt_trip_id) AS total_trips,
    "period",
    ROUND(AVG(drivetime), 3) AS drivetime,
    ROUND(AVG(dwelltime), 3) AS dwelltime,
    ROUND(AVG(signaldelay), 3) AS signaldelay,
    COALESCE(ROUND(AVG(dwelltime), 3), 0) +
    COALESCE(ROUND(AVG(signaldelay), 3), 0) +
    COALESCE(ROUND(AVG(drivetime), 3), 0) AS traveltime,
    ROUND(AVG(tspsavings), 3) AS tspsavings
  FROM
    trip_level
  GROUP BY
    "period"
)
SELECT
  total_trips,
  "period",
  {f_lag__drivetime} AS drivetime,
  {f_lag__dwelltime} AS dwelltime,
  {f_lag__signaldelay} AS signaldelay,
  {f_lag__traveltime} AS traveltime,
  {f_lag__tspsavings} AS tspsavings
FROM
  agg_travel_time