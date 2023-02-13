CREATE MATERIALIZED VIEW mv_drive_time AS WITH -- Aggregate signal delay for each stop-to-stop segment
signal_delay_segments AS (
  SELECT
    agency_id,
    trip_instance_id,
    "segment",
    SUM(COALESCE(signal_delay, 0)) AS signal_delay
  FROM
    mv_signal_delay
  GROUP BY
    agency_id,
    trip_instance_id,
    "segment"
),
drive_time_segments AS (
  SELECT
    agency_id,
    trip_instance_id,
    "segment",
    ANY_VALUE(trip_id) AS trip_id,
    ANY_VALUE(trip_start_time) AS trip_start_time,
    ANY_VALUE(trip_start_date) AS trip_start_date,
    ANY_VALUE(route_id) AS route_id,
    ANY_VALUE(trip_direction_id) AS trip_direction_id,
    ANY_VALUE(stop_start_id) AS stop_start_id,
    ANY_VALUE(stop_end_id) AS stop_end_id,
    MIN("timestamp") AS timestamp_start,
    MAX("timestamp") AS timestamp_end,
    AVG(speed) AS avg_speed,
    EXTRACT(
      EPOCH
      FROM
        timestamp_end - timestamp_start
    ) AS segment_duration
  FROM
    segment_events
  GROUP BY
    agency_id,
    trip_instance_id,
    "segment"
)
SELECT
  dts. *,
  -- Metrics
  COALESCE(sds.signal_delay, 0) AS signal_delay,
  segment_duration - COALESCE(signal_delay, 0) AS drive_time
FROM
  drive_time_segments dts
  LEFT JOIN signal_delay_segments sds USING (agency_id, trip_instance_id, "segment")
  LEFT JOIN mv_gtfs_dates gd ON dts.agency_id = gd.agency
  AND dts.trip_start_date = gd.date
  LEFT JOIN mv_gtfs_segments gs ON dts.agency_id = gs.agency_id
  AND gd.gtfs_date = gs.date
  AND dts.trip_id = gs.trip_id -- Only take segments matching GTFS segments
  AND dts.stop_start_id = gs.stop_start_id
  AND dts.stop_end_id = gs.stop_end_id