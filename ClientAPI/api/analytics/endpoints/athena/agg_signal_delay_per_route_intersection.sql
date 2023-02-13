-- agg_signal_delay_per_route_intersection
WITH filtered AS (
  SELECT
    locationid,
    locationname,
    signaldelay::FLOAT AS signaldelay,
    f_date_range_period(
      f_prior_date_range_start(%(start_date)s::DATE, %(end_date)s::DATE),
      %(start_date)s::DATE,
      "timestamp"::DATE
    ) AS "period",
    gtt_trip_id
  FROM
    public.v_signal_delay
  WHERE
    agency = %(agency)s
    AND "date" BETWEEN f_prior_date_range_start(
      %(start_date)s::DATE,
      %(end_date)s::DATE
    )
    AND %(end_date)s
    AND route = %(route)s
    AND trip_direction_id = ANY(%(direction_ids)s)
    AND {f_timeperiod} = ANY(%(selected_timeperiod)s)
    AND signaldelay < 300
),
per_location AS (
  SELECT
    COUNT(DISTINCT gtt_trip_id) AS num_trips,
    locationid,
    "period",
    ROUND(AVG(signaldelay), 5) AS signaldelay,
    locationname
  FROM
    filtered
  GROUP BY
    locationid,
    locationname,
    "period"
)
SELECT
  num_trips,
  {f_lag__signal_delay} AS signaldelay,
  "period",
  locationid,
  locationname
FROM
  per_location
ORDER BY
  "period"
