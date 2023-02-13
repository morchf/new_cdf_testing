CREATE
OR REPLACE PROCEDURE sp_evp_events () AS $$ BEGIN
  DROP TABLE IF EXISTS staging__evp_events;

RAISE INFO 'Creating \'evp_events\' staging table from CVP data';

CREATE TEMP TABLE staging__evp_events AS WITH vehicle_positions AS (
  SELECT
    *,
    CASE
      WHEN intersection_id IS NOT NULL THEN 'AT_INTERSECTION'
      ELSE 'IN_TRANSIT_TO'
    END AS current_status
  FROM
    staging__intersection_positions
),
segment_start_events AS (
  SELECT
    *,
    CASE
      WHEN current_status = 'AT_INTERSECTION' THEN (
        COALESCE(
          LAG(intersection_id) OVER (
            PARTITION BY agency_id,
            trip_instance_id,
            current_status
            ORDER BY
              "timestamp"
          ),
          ''
        ) <> intersection_id
      )
      AND COALESCE(
        EXTRACT(
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
        ) < 30,
        TRUE
      )
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
        current_status = 'AT_INTERSECTION'
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
        WHEN current_status = 'AT_INTERSECTION' THEN intersection_id
        ELSE NULL
      END
    ) AS intersection_start_id
  FROM
    segments
  GROUP BY
    agency_id,
    trip_instance_id,
    "segment"
),
intersection_to_intersection AS (
  SELECT
    *,
    LEAD(intersection_start_id) OVER (
      PARTITION BY agency_id,
      trip_instance_id
      ORDER BY
        "segment"
    ) AS intersection_end_id
  FROM
    segment_start
),
evp_events AS (
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
    iti.intersection_start_id,
    iti.intersection_end_id
  FROM
    segments s
    JOIN intersection_to_intersection iti USING (agency_id, trip_instance_id, "segment")
)
SELECT
  *
FROM
  evp_events;

-- WHERE
-- Handle beginning segment before reaching the first stop
-- intersection_start_id <> intersection_end_id;
END;

$$ LANGUAGE plpgsql;