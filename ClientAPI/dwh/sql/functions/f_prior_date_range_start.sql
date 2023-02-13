/*
  Map date range to start of prior date range of the same length
*/
CREATE OR REPLACE
FUNCTION f_prior_date_range_start (
  DATE, -- First date start
  DATE -- Second date start
) RETURNS DATE STABLE
AS $$
  SELECT (
    TO_CHAR(
      f_nth_period(
        -1,
        'day',
        $1::TIMESTAMP,
        $2::TIMESTAMP
      ),
      'YYYY-MM-DD'
    )
  )::DATE
$$ LANGUAGE SQL;