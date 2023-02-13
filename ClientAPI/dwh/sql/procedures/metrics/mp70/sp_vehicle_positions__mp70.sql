CREATE
OR REPLACE PROCEDURE sp_vehicle_positions__mp70 (p_agency_id TEXT, p_utc_date TEXT) AS $$ BEGIN
  RAISE INFO 'Creating \'vehicle_positions\' staging table';

DROP TABLE IF EXISTS staging__vehicle_positions;

-- Load vehicle logs into temporary table
CREATE TEMP TABLE staging__vehicle_positions AS WITH params AS (
  SELECT
    device_utc_date
  FROM
    mv_evp_dates
  WHERE
    agency_id = p_agency_id
    AND utc_date = p_utc_date
),
devices AS (
  SELECT
    *
  FROM
    ext_evp.devices AS d (
      public_ip,
      "description",
      agency,
      device_serial_number,
      gtt_serial_number,
      lan_ip,
      make,
      model,
      imei,
      mac_address,
      factory_default_pw,
      sim_serial
    )
  WHERE
    agency_id = p_agency_id
    AND utc_date = (
      SELECT
        device_utc_date
      FROM
        params
    )
),
vehicle_logs AS (
  SELECT
    m.glat AS latitude,
    m.glon AS longitude,
    m.gspd AS speed,
    m.utcTime AS "timestamp",
    m.utcdate AS trip_start_date,
    m. *,
    d. *,
    (
      speed = 0
      AND LAG(speed) OVER (
        PARTITION BY trip_start_date,
        vehsn
        ORDER BY
          "timestamp"
      ) = 0
    ) AS is_stopped
  FROM
    ext_analytics.mp70 m
    INNER JOIN devices d ON m.vehsn = d.device_serial_number
  WHERE
    m.utcdate = p_utc_date
    AND glat IS NOT NULL
    AND glon IS NOT NULL
    AND f_lightbar_on(gpi) = 1
),
moving_logs AS (
  SELECT
    *,
    SUM((NOT is_stopped) :: INT) OVER (
      PARTITION BY trip_start_date,
      vehsn
      ORDER BY
        "timestamp" ROWS UNBOUNDED PRECEDING
    ) AS stopped_segment
  FROM
    vehicle_logs
),
moving_blocks AS (
  SELECT
    *,
    EXTRACT(
      EPOCH
      FROM
        MAX("timestamp") OVER (
          PARTITION BY trip_start_date,
          vehsn,
          stopped_segment
        ) - MIN("timestamp") OVER (
          PARTITION BY trip_start_date,
          vehsn,
          stopped_segment
        )
    ) AS stopped_segment_duration
  FROM
    moving_logs
),
separated_blocks AS (
  SELECT
    *,
    EXTRACT(
      EPOCH
      FROM
        "timestamp" - LAG("timestamp") OVER (
          PARTITION BY trip_start_date,
          vehsn
          ORDER BY
            "timestamp"
        )
    ) AS timestamp_diff
  FROM
    moving_blocks
  WHERE
    stopped_segment_duration < 300
),
events AS (
  SELECT
    SUM((timestamp_diff > 30) :: INT) OVER (
      PARTITION BY trip_start_date,
      vehsn
      ORDER BY
        "timestamp" ROWS UNBOUNDED PRECEDING
    ) AS trip_segment,
    *
  FROM
    separated_blocks
),
trips AS (
  SELECT
    *,
    MIN("timestamp") OVER (
      PARTITION BY trip_start_date,
      vehsn,
      trip_segment
    ) AS trip_start_time,
    EXTRACT(
      EPOCH
      FROM
        (
          MAX("timestamp") OVER (
            PARTITION BY trip_start_date,
            vehsn,
            trip_segment
          ) - MIN("timestamp") OVER (
            PARTITION BY trip_start_date,
            vehsn,
            trip_segment
          )
        )
    ) AS trip_duration
  FROM
    events
)
SELECT
  *,
  vehsn || '_t-' || trip_segment || '_' || trip_start_time AS trip_instance_id
FROM
  trips
WHERE
  -- Filter segments too short to be a trip
  trip_duration > 10;

END;

$$ LANGUAGE plpgsql;