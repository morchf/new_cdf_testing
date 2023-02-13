/*
  Wraps the `DATEDIFF` function to allow dynamic date parts using a subset of the
  available date part identifiers

  See: https://docs.aws.amazon.com/redshift/latest/dg/r_DATEDIFF_function.html

  Args:
    VARCHAR: Granularity to map the difference between passed-in timestamps
    TIMESTAMP: First timestamp
    TIMESTAMP: Second timestamp
 */
CREATE
OR REPLACE FUNCTION f_date_diff (
  TEXT,      -- Period
  TIMESTAMP, -- First timestamp
  TIMESTAMP  -- Second timestamp
)
RETURNS BIGINT STABLE
AS $$
  SELECT
    CASE
      WHEN $1 IN ('day', 'days', 'd') THEN DATEDIFF(DAY, $2, $3)
      WHEN $1 IN ('week', 'weeks', 'w') THEN DATEDIFF(WEEK, $2, $3)
      WHEN $1 IN ('year', 'years', 'y', 'yr', 'yrs') THEN DATEDIFF(YEAR, $2, $3)
      WHEN $1 IN ('quarter', 'quarters', 'qtr', 'qtrs') THEN DATEDIFF(QTR, $2, $3)
      WHEN $1 IN ('hour', 'hours', 'h', 'hr', 'hrs') THEN DATEDIFF(HOUR, $2, $3)
      WHEN $1 IN ('minute', 'minutes', 'm', 'min', 'mins') THEN DATEDIFF(MIN, $2, $3)
      WHEN $1 IN ('second', 'seconds', 's', 'sec', 'secs') THEN DATEDIFF(SEC, $2, $3)
      ELSE 0
    END
$$ LANGUAGE SQL;
