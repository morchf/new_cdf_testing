CREATE
OR REPLACE FUNCTION f_nth_period (
  INT,       -- Number of periods removed
  TEXT,      -- Period
  TIMESTAMP, -- Start date
  TIMESTAMP  -- End date
) RETURNS TIMESTAMP STABLE
AS $$
  SELECT f_date_add($2, $1 * (f_date_diff($2, $3, $4)::INT + 1), $3)::TIMESTAMP
$$ LANGUAGE SQL;
