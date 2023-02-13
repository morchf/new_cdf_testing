/*
  Map date to prior or current date range
*/
CREATE OR REPLACE
FUNCTION f_date_range_period (
  DATE, -- Prior date start
  DATE, -- Current date start
  DATE  -- Date
) RETURNS TEXT STABLE
AS $$
  SELECT (
    TO_CHAR(
      CASE
        -- Map dates after current to current
        WHEN $3 >= $2 THEN $2

        -- Map dates before current to prior
        ELSE $1
      END,
      'YYYY-MM-DD'
    )
  )
$$ LANGUAGE SQL;