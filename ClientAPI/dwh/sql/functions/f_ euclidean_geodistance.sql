/*
 * Allow comparison of point to line for close coordinates
 */
CREATE OR REPLACE FUNCTION f_euclidean_geodistance (
  geo1 GEOMETRY,
  geo2 GEOMETRY
) RETURNS FLOAT IMMUTABLE AS $$ 
SELECT  ST_Distance(
    $1,
    $2
  ) * 111139
$$ LANGUAGE sql;