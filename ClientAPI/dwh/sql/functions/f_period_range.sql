/*
  Map date to either the current date range or the period before the start date
  with the same length of time between the passed-in date range

  Args:
    TEXT: Granularity to map the length of the selected date range
    TIMESTAMP: Start of the date range
    TIMESTAMP: End of the date range
    TIMESTAMP: Date
*/
CREATE OR REPLACE
FUNCTION f_period_range (
  TEXT,      -- Period
  TIMESTAMP, -- Start date
  TIMESTAMP, -- End date
  TIMESTAMP  -- Value
) RETURNS TIMESTAMP STABLE
AS $$
  SELECT (
    CASE
      -- Map dates after start to the start range
      WHEN $4 > $2 THEN $2
      
      -- Map dates before to the prior period
      ELSE
        f_date_add(
          $1,
          f_date_diff($1, $3, $2)::INT,
          $2
        )
    END
  )::TIMESTAMP
$$ LANGUAGE SQL;
