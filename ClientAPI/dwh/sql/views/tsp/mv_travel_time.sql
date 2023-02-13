CREATE MATERIALIZED VIEW mv_travel_time AS WITH drive_time_ordered AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY agency_id,
      trip_start_date,
      trip_start_time,
      trip_id,
      stop_start_id
      ORDER BY
        timestamp_start
    ) AS repeat_stop_start_order,
    ROW_NUMBER() OVER (
      PARTITION BY agency_id,
      trip_start_date,
      trip_start_time,
      stop_end_id
      ORDER BY
        timestamp_start
    ) AS repeat_stop_end_order
  FROM
    mv_drive_time
  WHERE
    route_id IS NOT NULL
),
drive_time AS (
  SELECT
    drt.agency_id,
    drt.trip_start_time,
    drt.trip_start_date,
    drt.route_id,
    drt.trip_direction_id,
    drt.trip_id,
    -- TODO: Remove
    dwts.stop_id AS stopstartid,
    dwts.timestamp_start AS stopstarttime,
    dwts.stop_lat AS stopstartlatitude,
    dwts.stop_lon AS stopstartlongitude,
    dwts.stop_name AS stopstart,
    dwte.stop_id AS stopendid,
    dwte.timestamp_end AS stopendtime,
    dwte.stop_lat AS stopendlatitude,
    dwte.stop_lon AS stopendlongitude,
    dwte.stop_name AS stopend,
    -- Use segment-start dwell time
    dwts.dwell_time,
    drt.drive_time,
    drt.signal_delay
  FROM
    drive_time_ordered drt
    LEFT OUTER JOIN mv_dwell_time dwts ON drt.agency_id = dwts.agency_id
    AND drt.trip_start_date = dwts.trip_start_date
    AND drt.trip_start_time = dwts.trip_start_time
    AND drt.trip_id = dwts.trip_id
    AND drt.stop_start_id = dwts.stop_id
    AND drt.repeat_stop_start_order = dwts.repeat_stop_order
    LEFT OUTER JOIN mv_dwell_time dwte ON drt.agency_id = dwte.agency_id
    AND drt.trip_start_date = dwte.trip_start_date
    AND drt.trip_start_time = dwte.trip_start_time
    AND drt.trip_id = dwte.trip_id
    AND drt.stop_end_id = dwte.stop_id
    AND drt.repeat_stop_end_order = dwte.repeat_stop_order
)
SELECT
  agency_id AS agency,
  trip_start_date AS "date",
  route_id AS route,
  CASE
    WHEN trip_direction_id = 0 then 'outbound'
    WHEN trip_direction_id = 1 then 'inbound'
  END AS direction,
  trip_start_time AS tripstarttime,
  trip_id || '_' || trip_start_time AS gtt_trip_id,
  -- TODO: Remove
  stopstartid,
  stopstarttime,
  stopstartlatitude,
  stopstartlongitude,
  stopstart,
  stopendid,
  stopendtime,
  stopendlatitude,
  stopendlongitude,
  stopend,
  -- Metrics
  ANY_VALUE(COALESCE(dwell_time, 0)) AS dwelltime,
  ANY_VALUE(COALESCE(drive_time, 0)) AS drivetime,
  ANY_VALUE(COALESCE(signal_delay, 0)) AS signaldelay,
  ANY_VALUE(COALESCE(dwell_time, 0)) + ANY_VALUE(COALESCE(drive_time, 0)) + ANY_VALUE(COALESCE(signal_delay, 0)) AS traveltime,
  0 AS tspsavings
FROM
  drive_time
WHERE
  stopstarttime IS NOT NULL
  AND stopendtime IS NOT NULL
GROUP BY
  agency_id,
  trip_start_date,
  route_id,
  trip_direction_id,
  trip_id,
  trip_start_time,
  stopstartid,
  stopstarttime,
  stopstartlatitude,
  stopstartlongitude,
  stopstart,
  stopendid,
  stopendtime,
  stopendlatitude,
  stopendlongitude,
  stopend