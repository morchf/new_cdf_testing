/*
  Map date to date/time bands of the passed in period and period length, using
  the start date as a reference

  Args:
    TEXT: Granularity to map the different bands
    INT: Number of periods to include in a band
    TIMESTAMP: Start of the date range
    TIMESTAMP: End of the date range
    TIMESTAMP: Date

  Example:
    Map times to bands of 3 hours each, starting at 2021-09-04 00:00:00. 

    f_time_bands(
      'hour',
      3,
      '2021-09-04'::TIMESTAMP,
      x::TIMESTAMP
    )

    x = 2021-09-04 01:00:00 -> 2021-09-04 00:00:00.000
    x = 2021-09-04 03:00:00 -> 2021-09-04 03:00:00.000
    x = 2021-09-04 07:00:00 -> 2021-09-04 06:00:00.000
    x = 2021-09-03 23:00:00 -> 2021-09-03 21:00:00.000
*/
CREATE OR REPLACE
FUNCTION f_time_bands (
  TEXT,      -- Period
  INT,       -- Frequency
  TIMESTAMP, -- Start date
  TIMESTAMP  -- Value 
) RETURNS TIMESTAMP STABLE
AS $$
  SELECT
    f_date_add(
      $1,
      (
        -- Calculate number of bands away from start date
        FLOOR(
          f_date_diff($1, $3, $4)::FLOAT
          / $2
        ) * $2
      )::INT,
      $3
    )::TIMESTAMP
$$ LANGUAGE SQL
