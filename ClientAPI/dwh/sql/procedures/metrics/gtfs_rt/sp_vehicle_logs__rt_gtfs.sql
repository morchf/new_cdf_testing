CREATE
OR REPLACE PROCEDURE sp_vehicle_logs__rt_gtfs (p_agency TEXT, p_date TEXT) AS $$
DECLARE
  l_agency_id TEXT;

BEGIN
  RAISE INFO 'Creating \'vehicle_logs\' staging table';

SELECT
  INTO l_agency_id agency_id
FROM
  cfg_agency
WHERE
  agency = p_agency;

DROP TABLE IF EXISTS staging__vehicle_logs;

-- Load vehicle logs into temporary table
CREATE TEMP TABLE staging__vehicle_logs AS -- Map continuous blocks of trips
WITH vehicle_positions AS (
  SELECT
    agency_id,
    entity_id,
    current_stop_sequence,
    stop_id AS rt_stop_id,
    current_status,
    congestion_level,
    occupancy_status,
    vehicle_id,
    vehicle_label,
    license_plate,
    latitude :: FLOAT,
    longitude :: FLOAT,
    bearing,
    odometer,
    -- m / s -> MPH
    (speed :: FLOAT) * 2.23694 AS speed,
    trip_id,
    route_id,
    trip_direction_id,
    TIMESTAMP 'epoch' + ("timestamp" :: INT) * INTERVAL '1 second' AS utc_timestamp,
    (trip_start_date :: DATE) + (trip_start_time :: TIME) AS trip_start_time,
    (trip_start_date :: DATE) AS trip_start_date,
    schedule_relationship,
    stop_id,
    'RT_GTFS' :: TEXT AS source_device
  FROM
    ext_tsp.rt_gtfs_vehicle_positions vp
  WHERE
    vp.agency_id = l_agency_id -- TODO: Update to filter by 'utc_date' partition once partitioned by record timestamp
    AND (trip_start_date :: DATE) = (p_date :: DATE)
    AND "timestamp" <> 0
),
trip_blocks AS (
  SELECT
    agency_id,
    trip_start_date,
    vehicle_id,
    trip_id,
    route_id,
    trip_direction_id,
    trip_start_time,
    MIN(utc_timestamp) AS min_utc_timestamp,
    MAX(utc_timestamp) AS max_utc_timestamp,
    trip_start_time - min_utc_timestamp AS utc_diff
  FROM
    vehicle_positions
  GROUP BY
    agency_id,
    trip_start_date,
    vehicle_id,
    trip_start_time,
    trip_id,
    route_id,
    trip_direction_id
),
rt_radio_logs AS (
  SELECT
    -- Trip block
    tb.trip_start_date,
    tb.trip_start_time,
    tb.vehicle_id,
    tb.trip_id,
    tb.route_id,
    tb.trip_direction_id,
    -- Fields
    Latitude AS latitude,
    Longitude AS longitude,
    -- f_decode_longitude(originalrtradiomsg) AS longitude,
    -- m / 5 seconds -> MPH
    (Speed :: FLOAT) * 2.23694 / 5 AS speed,
    ioT_timestamp :: TIMESTAMP AS utc_timestamp,
    source_device :: TEXT,
    -- Unused fields
    CMSId,
    GTTSerial,
    UnitId,
    RSSI,
    Heading,
    VehicleGPSCStat,
    VehicleGPSCSatellites,
    VehicleVID,
    AgencyCode,
    VehicleModeStatus,
    VehicleTurnStatus,
    VehicleOpStatus,
    VehicleClass,
    ConditionalPriority,
    VehicleDiagnosticValue,
    VehicleName,
    DeviceName,
    device_timestamp
  FROM
    ext_analytics.rt_radio_messages rrm
    LEFT JOIN trip_blocks tb ON rrm.agency_id = tb.agency_id
    AND (rrm.utc_date :: DATE) = tb.trip_start_date
    AND rrm.vehiclevid = tb.vehicle_id
    AND (
      TO_CHAR(ioT_timestamp :: TIMESTAMP, 'HH24:MI:SS') BETWEEN TO_CHAR(tb.min_utc_timestamp, 'HH24:MI:SS')
      AND TO_CHAR(tb.max_utc_timestamp, 'HH24:MI:SS')
    )
  WHERE
    rrm.agency_id = l_agency_id
    AND utc_date = p_date
    AND trip_id IS NOT NULL
),
combined_logs AS (
  -- Can combine RT GTFS with RT Radio messages if necessary
  SELECT
    utc_timestamp,
    -- TODO: Change to agency ID
    p_agency AS agency_id,
    NULL AS entity_id,
    NULL AS current_stop_sequence,
    NULL AS rt_stop_id,
    NULL AS current_status,
    NULL AS congestion_level,
    NULL AS occupancy_status,
    vehicle_id,
    NULL AS vehicle_label,
    NULL AS license_plate,
    latitude,
    longitude,
    NULL AS bearing,
    NULL AS odometer,
    speed,
    trip_id,
    route_id,
    trip_direction_id,
    trip_start_time,
    trip_start_date,
    NULL AS schedule_relationship,
    source_device
  FROM
    rt_radio_logs
  UNION
  ALL (
    SELECT
      utc_timestamp,
      -- TODO: Change to agency ID
      p_agency AS agency_id,
      vp.entity_id,
      vp.current_stop_sequence,
      vp.stop_id AS rt_stop_id,
      vp.current_status,
      vp.congestion_level,
      vp.occupancy_status,
      vp.vehicle_id,
      vp.vehicle_label,
      vp.license_plate,
      vp.latitude,
      vp.longitude,
      vp.bearing,
      vp.odometer,
      -- Speed all = 0
      NULL AS speed,
      vp.trip_id,
      vp.route_id,
      vp.trip_direction_id,
      vp.trip_start_time,
      vp.trip_start_date,
      vp.schedule_relationship,
      vp.source_device
    FROM
      vehicle_positions vp
      JOIN trip_blocks tb USING (
        agency_id,
        trip_start_date,
        vehicle_id,
        trip_start_time,
        trip_id,
        route_id,
        trip_direction_id
      )
  )
),
-- Extracts timezone from trip information
timezone_diff AS (
  SELECT
    ROUND(
      EXTRACT(
        EPOCH
        FROM
          AVG(utc_diff)
      ) / 3600,
      0
    ) :: INT * 3600 AS utc_diff
  FROM
    trip_blocks
)
SELECT
  *,
  DATEADD(
    SEC,
    (
      SELECT
        utc_diff
      FROM
        timezone_diff
    ),
    utc_timestamp
  ) AS "timestamp",
  vehicle_id || '_' || trip_start_date || '_' || trip_id || '_' || trip_start_time AS trip_instance_id
FROM
  combined_logs;

END;

$$ LANGUAGE plpgsql;