CREATE MATERIALIZED VIEW mv_evp_corridor_trips AS WITH intersection_events AS (
  SELECT agency_id,
    trip_start_date,
    trip_instance_id,
    intersection_id,
    MIN("timestamp") as start_timestamp
  FROM evp_events
  GROUP BY agency_id,
    trip_start_date,
    trip_instance_id,
    intersection_id
),
trip_events AS (
  SELECT agency_id,
    trip_start_date,
    trip_instance_id,
    LISTAGG(intersection_id, ',') WITHIN GROUP (
      ORDER BY start_timestamp
    ) AS location_ids
  FROM intersection_events
  GROUP BY agency_id,
    trip_start_date,
    trip_instance_id
)
SELECT te.*,
  COALESCE(
    c.corridor_id,
    'INT SEQ ' || REPLACE(te.location_ids, ',', ' / ')
  ) AS corridor_id,
  c.corridor_name
FROM trip_events te
  LEFT JOIN mv_evp_dates d ON d.agency_id = te.agency_id
  AND d.utc_date = te.trip_start_date
  LEFT OUTER JOIN mv_evp_corridors c ON te.agency_id = c.agency_id
  AND d.device_utc_date = c.utc_date
  AND c.location_ids = te.location_ids
WHERE te.location_ids IS NOT NULL