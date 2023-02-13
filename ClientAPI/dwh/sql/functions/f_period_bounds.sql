/*
  Map date to either the first or second date

  Args:
    DATE: Start of the date range
    DATE: End of the date range
    DATE: Date
*/
CREATE OR REPLACE
FUNCTION f_period_bounds (
  DATE, -- First date start
  DATE, -- Second date start
  DATE  -- Value
) RETURNS DATE STABLE
AS $$
  SELECT (
    CASE
      -- Map dates after end to the end range
      WHEN $3 >= $2 THEN $2

      -- Map dates before end to the start range
      ELSE $1
    END
  )ß
$$ LANGUAGE SQL;