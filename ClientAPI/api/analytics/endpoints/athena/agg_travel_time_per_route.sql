-- agg_travel_time_per_route
WITH filtered AS (
  SELECT
    dwelltime::FLOAT AS dwelltime,
    signaldelay::FLOAT AS signaldelay,
    drivetime::FLOAT AS drivetime,
    tspsavings::FLOAT AS tspsavings,
    f_date_range_period(
      f_prior_date_range_start(%(start_date)s::DATE, %(end_date)s::DATE),
      %(start_date)s::DATE,
      stopstarttime::DATE
    ) AS "period",
    f_format_name(stopstart) AS stopstartname,
    f_format_name(stopend) AS stopendname,
    stopstartid AS stopstart_id,
    stopendid AS stopend_id,
    stopstartlatitude,
    stopstartlongitude,
    stopendlatitude,
    stopendlongitude,
    gtt_trip_id
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
segment_level AS (
  SELECT
    COUNT(DISTINCT gtt_trip_id) AS num_trips,
    "period",
    stopstartname,
    stopendname,
    stopstart_id,
    stopend_id,
    ROUND(AVG(stopstartlatitude), 5) AS stopstartlatitude,
    ROUND(AVG(stopstartlongitude), 5) AS stopstartlongitude,
    ROUND(AVG(stopendlatitude), 5) AS stopendlatitude,
    ROUND(AVG(stopendlongitude), 5) AS stopendlongitude,
    ROUND(AVG(tspsavings), 3) AS tspsavings,
    ROUND(AVG(drivetime), 3) AS drivetime,
    ROUND(AVG(dwelltime), 3) AS dwelltime,
    ROUND(AVG(signaldelay), 3) AS signaldelay,
    COALESCE(ROUND(AVG(dwelltime), 3), 0)
    + COALESCE(ROUND(AVG(signaldelay), 3), 0)
    + COALESCE(ROUND(AVG(drivetime), 3), 0) AS traveltime
  FROM
    filtered
  GROUP BY
    stopstartname,
    stopendname,
    stopstart_id,
    stopend_id,
    "period"
)
SELECT
  -- Location
  num_trips,
  stopstartname,
  stopstart_id,
  stopendname,
  stopend_id,
  stopstartlatitude,
  stopstartlongitude,
  stopendlatitude,
  stopendlongitude,
  "period",
  -- Metrics
  {f_lag__dwelltime} AS dwelltime,
  {f_lag__traveltime} AS traveltime,
  {f_lag__drivetime} AS drivetime,
  {f_lag__signaldelay} AS signaldelay,
  {f_lag__tspsavings} AS tspsavings
FROM
  segment_level
ORDER BY
  stopstartname,
  stopendname,
  "period"
