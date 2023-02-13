/*
 Map sequential event types to a proper duration
 
 Args:
 TEXT: Prior status
 TEXT: Current status
 TEXT: Next status
 
 TIMESTAMP: Prior timestamp
 TIMESTAMP: Current timestamp
 TIMESTAMP: Next timestamp
 */
CREATE
OR REPLACE FUNCTION f_duration (
  /* Sequential status */
  prior_status TEXT,
  current_status TEXT,
  next_status TEXT,
  /* Sequential timestamp */
  prior_timestamp TIMESTAMP,
  "current_timestamp" TIMESTAMP,
  next_timestamp TIMESTAMP
) RETURNS FLOAT STABLE AS $$
SELECT
  EXTRACT (
    MS
    FROM
      CASE
      	/* Stop / intersection */
        WHEN $2 <> 'IN_TRANSIT_TO' THEN CASE
          WHEN $3 <> $2 THEN '0' :: INTERVAL
          ELSE $6 - $5
        END
        /* Last event in series */
        WHEN $3 IS NULL THEN CASE
          WHEN $1 <> 'IN_TRANSIT_TO' THEN $5 - $4
          ELSE '0' :: INTERVAL
        END
        /* Border to stop/intersection events. Not first in series */
        WHEN $1 IS NOT NULL AND $1 <> 'IN_TRANSIT_TO' THEN $6 - $4
        /* Drive events */
        ELSE $6 - $5
      END
  ) / 1000.
$$ LANGUAGE SQL;
