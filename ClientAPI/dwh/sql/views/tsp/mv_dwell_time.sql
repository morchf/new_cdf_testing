CREATE MATERIALIZED VIEW mv_dwell_time AS WITH dwell_time AS (
  SELECT
    se.agency_id,
    se.trip_start_date,
    se.trip_start_time,
    se.trip_id,
    se.stop_id,
    se.route_id,
    se.trip_direction_id,
    se.segment,
    MIN("timestamp") AS timestamp_start,
    MIN("timestamp") AS timestamp_end,
    AVG(speed) AS avg_speed,
    SUM(COALESCE("duration", 0)) AS dwell_time,
    CASE
      WHEN COUNT(DISTINCT current_status) = 1 THEN ANY_VALUE(current_status)
      ELSE 'STOPPED_AT'
    END AS event_type
  FROM
    segment_events se
  WHERE
    (
      current_status = 'STOPPED_AT'
      OR current_status = 'NEAR_STOP'
    )
  GROUP BY
    agency_id,
    trip_start_date,
    trip_start_time,
    trip_direction_id,
    se.route_id,
    se.trip_id,
    se.stop_id,
    "segment"
)
SELECT
  dt. *,
  stops.stop_name,
  stops.stop_lat,
  stops.stop_lon,
  ROW_NUMBER() OVER (
    PARTITION BY dt.agency_id,
    dt.trip_start_date,
    dt.trip_start_time,
    dt.trip_id,
    dt.stop_id
    ORDER BY
      timestamp_start
  ) AS repeat_stop_order
FROM
  dwell_time dt
  LEFT JOIN mv_gtfs_dates gd ON dt.agency_id = gd.agency
  AND dt.trip_start_date = gd.date
  LEFT JOIN mv_gtfs_stops stops ON stops.agency = dt.agency_id
  AND stops.date = gd.gtfs_date
  AND stops.stop_id = dt.stop_id
  AND stops.trip_id = dt.trip_id