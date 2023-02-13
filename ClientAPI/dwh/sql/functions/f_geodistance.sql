CREATE OR REPLACE FUNCTION f_geodistance (
  latitude1  float8,
  longitude1 float8,
  latitude2  float8,
  longitude2 float8
) RETURNS float8 IMMUTABLE AS $$ 
SELECT asin(
  sqrt(
    sin(radians($3-$1)/2)^2 +
    sin(radians($4-$2)/2)^2 *
    cos(radians($1)) *
    cos(radians($3))
  )
) * 7926.3352 AS distance
$$ LANGUAGE sql;