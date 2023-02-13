/*
 Wraps the `DATEADD` function to allow dynamic date parts using a subset of the
 available date part identifiers
 
 See: https://docs.aws.amazon.com/redshift/latest/dg/r_DATEADD_function.html
 */
CREATE
OR REPLACE FUNCTION f_date_add (
  TEXT,     -- Period
  INT,      -- Number of periods
  TIMESTAMP -- Date
)
RETURNS TIMESTAMP STABLE
AS $$
  SELECT
    CASE
      WHEN $1 IN ('day', 'days', 'd') THEN DATEADD(DAY, $2, $3)
      WHEN $1 IN ('week', 'weeks', 'w') THEN DATEADD(WEEK, $2, $3)
      WHEN $1 IN ('year', 'years', 'y', 'yr', 'yrs') THEN DATEADD(YEAR, $2, $3)
      WHEN $1 IN ('quarter', 'quarters', 'qtr', 'qtrs') THEN DATEADD(QTR, $2, $3)
      WHEN $1 IN ('hour', 'hours', 'h', 'hr', 'hrs') THEN DATEADD(HOUR, $2, $3)
      WHEN $1 IN ('minute', 'minutes', 'm', 'min', 'mins') THEN DATEADD(MIN, $2, $3)
      WHEN $1 IN ('second', 'seconds', 's', 'sec', 'secs') THEN DATEADD(SEC, $2, $3)
      ELSE $3
    END
$$ LANGUAGE SQL;
