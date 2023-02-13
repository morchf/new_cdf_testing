CREATE
OR REPLACE FUNCTION f_kepler (geo GEOMETRY) RETURNS VARCHAR STABLE AS $$
SELECT
    '{"type": "FeatureCollection","features": [{"type": "Feature","geometry":' || ST_AsGeoJson($1) :: TEXT || '}]}' $$ LANGUAGE SQL;