-- agg_travel_time
WITH filtered AS (
  SELECT
    route,
    "date",
    gtt_trip_id,
    drivetime::FLOAT AS drivetime,
    dwelltime::FLOAT AS dwelltime,
    signaldelay::FLOAT AS signaldelay,
    traveltime::FLOAT AS traveltime,
    tspsavings::FLOAT AS tspsavings
  FROM
    public.mv_travel_time
  WHERE
    agency = %(agency)s
    AND "date" BETWEEN %(start_date)s
    AND %(end_date)s
    AND direction = ANY(%(selected_direction)s)
    AND {f_timeperiod} = ANY(%(selected_timeperiod)s)
),
trip_level AS (
  SELECT
    ANY_VALUE(route) AS route,
    ANY_VALUE("date") AS "date",
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
  ANY_VALUE(route) AS route,
  MAX("date") AS last_updated,
  ROUND(AVG(drivetime), 3) AS drivetime,
  ROUND(AVG(dwelltime), 3) AS dwelltime,
  ROUND(AVG(signaldelay), 3) AS signaldelay,
  COALESCE(ROUND(AVG(dwelltime), 3), 0) + COALESCE(ROUND(AVG(signaldelay), 3), 0) + COALESCE(ROUND(AVG(drivetime), 3), 0) AS traveltime
FROM
  trip_level
GROUP BY
  route