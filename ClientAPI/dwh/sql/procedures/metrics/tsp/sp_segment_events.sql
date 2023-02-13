CREATE
OR REPLACE PROCEDURE sp_segment_events () AS $$ BEGIN
  DROP TABLE IF EXISTS staging__segment_events;

RAISE INFO 'Creating \'segment_events\' staging table';

CREATE TEMP TABLE staging__segment_events AS WITH vehicle_positions AS (
  SELECT
    *,
    CASE
      -- Take stopped events within distance of both intersections and stops as a bus stop event
      WHEN stop_id IS NOT NULL
      AND speed IS NOT NULL
      AND speed < 3.0 THEN 'STOPPED_AT'
      WHEN stop_id IS NOT NULL
      AND (
        is_closest
        OR speed IS NULL
      ) THEN 'NEAR_STOP'
      WHEN intersection_id IS NOT NULL
      AND (
        speed IS NULL
        OR speed < 3.0
      ) THEN 'AT_INTERSECTION'
      ELSE 'IN_TRANSIT_TO'
    END AS current_status
  FROM
    staging__intersection_positions
),
segment_start_events AS (
  SELECT
    *,
    CASE
      WHEN (
        current_status = 'STOPPED_AT'
        OR current_status = 'NEAR_STOP'
      ) THEN COALESCE(
        LAG(stop_id) OVER (
          PARTITION BY agency_id,
          trip_instance_id,
          current_status
          ORDER BY
            "timestamp"
        ),
        ''
      ) <> stop_id
      ELSE EXTRACT(
        'epoch'
        FROM
          (
            "timestamp" - LAG("timestamp") OVER (
              PARTITION BY agency_id,
              trip_instance_id,
              current_status
              ORDER BY
                "timestamp"
            )
          )
      ) > 30 -- Maximum frequency between GPS points
    END AS is_segment_start
  FROM
    vehicle_positions
),
segments AS (
  SELECT
    *,
    -- Drive segments
    SUM(
      (
        (
          current_status = 'STOPPED_AT'
          OR current_status = 'NEAR_STOP'
        )
        AND is_segment_start
      ) :: INT
    ) OVER (
      PARTITION BY agency_id,
      trip_instance_id
      ORDER BY
        "timestamp" ROWS UNBOUNDED PRECEDING
    ) AS "segment"
  FROM
    segment_start_events
),
segment_start AS (
  SELECT
    agency_id,
    trip_instance_id,
    "segment",
    -- Ignore NULL stop IDs
    MAX(
      CASE
        WHEN (
          current_status = 'STOPPED_AT'
          OR current_status = 'NEAR_STOP'
        ) THEN stop_id
        ELSE NULL
      END
    ) AS stop_start_id
  FROM
    segments
  GROUP BY
    agency_id,
    trip_instance_id,
    "segment"
),
stop_to_stop AS (
  SELECT
    *,
    LEAD(stop_start_id) OVER (
      PARTITION BY agency_id,
      trip_instance_id
      ORDER BY
        "segment"
    ) AS stop_end_id
  FROM
    segment_start
),
segment_events AS (
  SELECT
    s. *,
    f_duration(
      LAG(s.current_status) OVER (
        PARTITION BY s.agency_id,
        s.trip_instance_id
        ORDER BY
          s.timestamp
      ),
      current_status,
      LEAD(s.current_status) OVER (
        PARTITION BY s.agency_id,
        s.trip_instance_id
        ORDER BY
          s.timestamp
      ),
      LAG(s.timestamp) OVER (
        PARTITION BY s.agency_id,
        s.trip_instance_id
        ORDER BY
          s.timestamp
      ),
      "timestamp",
      LEAD(s.timestamp) OVER (
        PARTITION BY s.agency_id,
        s.trip_instance_id
        ORDER BY
          s.timestamp
      )
    ) AS "duration",
    -- Stop-to-stop
    sts.stop_start_id,
    sts.stop_end_id
  FROM
    segments s
    JOIN stop_to_stop sts USING (agency_id, trip_instance_id, "segment")
)
SELECT
  *
FROM
  segment_events -- Remove beginning segment before reaching the first stop
WHERE
  stop_start_id <> stop_end_id;

END;

$$ LANGUAGE plpgsql;