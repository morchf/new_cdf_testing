-- agg_travel_time_per_route_day
WITH filtered AS (
  SELECT
    *,
    f_period(%(period)s::VARCHAR, tripstarttime::DATE::VARCHAR) AS "period"
  FROM
    public.mv_travel_time
  WHERE
    agency = %(agency)s
    AND route = %(route)s
    AND "date" BETWEEN %(start_date)s
    AND %(end_date)s
    AND direction = ANY(%(selected_direction)s)
    AND {f_timeperiod} = ANY(%(selected_timeperiod)s)
),
trip_level AS (
  SELECT
    ANY_VALUE("period") AS "period",
    SUM(drivetime::FLOAT) AS drivetime,
    SUM(dwelltime::FLOAT) AS dwelltime,
    SUM(signaldelay::FLOAT) AS signaldelay,
    SUM(tspsavings::FLOAT) AS tspsavings
  FROM
    filtered
  GROUP BY
    gtt_trip_id
)
SELECT
  "period",
  ROUND(AVG(dwelltime), 3) AS dwelltime,
  ROUND(AVG(drivetime), 3) AS drivetime,
  ROUND(AVG(signaldelay), 3) AS signaldelay,
  ROUND(AVG(tspsavings), 3) AS tspsavings,
  COALESCE(ROUND(AVG(dwelltime), 3), 0)
  + COALESCE(ROUND(AVG(signaldelay), 3), 0)
  + COALESCE(ROUND(AVG(drivetime), 3), 0) AS traveltime
FROM
  trip_level
GROUP BY
  "period"
ORDER BY
  "period"