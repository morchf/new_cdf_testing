CREATE
OR REPLACE FUNCTION f_interpolate_linear (
  -- 1
  t TIMESTAMP,
  -- 2
  previous_t TIMESTAMP,
  -- 3
  previous_x FLOAT,
  -- 4
  previous_y FLOAT,
  -- 5
  previous_speed FLOAT,
  -- 6
  previous_heading FLOAT,
  -- 7
  next_t TIMESTAMP,
  -- 8
  next_x FLOAT,
  -- 9
  next_y FLOAT,
  -- 10
  next_speed FLOAT,
  -- 11
  next_heading FLOAT
) RETURNS SUPER STABLE AS $$
SELECT
  ARRAY(
    f_progress($2, $1, $7) * ($8 - $3) + $3,
    f_progress($2, $1, $7) * ($9 - $4) + $4
  ) $$ LANGUAGE SQL;

/*
 SELECT f_interpolate_linear(
 '2022-06-10 10:05:00' :: TIMESTAMP,
 '2022-06-10 10:00:00' :: TIMESTAMP,
 10::FLOAT,
 10::FLOAT,
 0::FLOAT,
 0::FLOAT,
 '2022-06-10 10:10:00'::TIMESTAMP,
 20::FLOAT,
 20::FLOAT,
 0::FLOAT,
 0::FLOAT
 )
 */