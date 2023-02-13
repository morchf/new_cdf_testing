/*
Mock a materialized view by recreating it as a temporary table
*/
CREATE OR REPLACE
PROCEDURE testing.sp_mock_mv(
  p_mv IN TEXT
)
AS $$
DECLARE 
  l_view_sql CHARACTER VARYING(10000);
  l_is_temp_table BOOL;
BEGIN
  RAISE INFO 'Building view definition';

  EXECUTE 'SELECT' ||
    ' SUBSTRING(' ||
    '   view_definition,' ||
    '   COALESCE(' ||
    '     CHARINDEX(\'AS\', view_definition),' ||
    '     CHARINDEX(\'as\', view_definition)' ||
    '   ) + 2' ||
    ' )' ||
    ' FROM information_schema.views' ||
    ' WHERE table_name = ' || QUOTE_LITERAL(p_mv) ||
    ' AND table_schema <> \'testing\''
  INTO l_view_sql;

  SELECT INTO l_is_temp_table
  COUNT(DISTINCT id) <> 0
  FROM stv_tbl_perm
  WHERE
    temp = 1
    AND name = p_mv;

  IF l_is_temp_table THEN
    EXECUTE 'DROP TABLE ' || p_mv;
  END IF;

  RAISE INFO 'Creating view %:%', p_mv, l_view_sql;

  EXECUTE ' CREATE TEMP TABLE ' || p_mv ||
    ' AS ' || l_view_sql;
 END;
$$ LANGUAGE plpgsql;
