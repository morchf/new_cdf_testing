/*
Mock a table's visibility in the 'public' schema
*/
CREATE OR REPLACE
PROCEDURE testing.sp_mock_table(
	p_table IN TEXT,
  p_signature IN CHARACTER VARYING(1024)
)
AS $$
DECLARE
  l_is_temp_table BOOL;
BEGIN
  SELECT INTO l_is_temp_table
  COUNT(DISTINCT id) <> 0
  FROM stv_tbl_perm
  WHERE
    temp = 1
    AND name = p_table;

  IF l_is_temp_table THEN
    EXECUTE 'DROP TABLE ' || p_table;
  END IF;

  EXECUTE 'CREATE TEMP TABLE ' || p_table || ' ' || p_signature;
 END;
$$ LANGUAGE plpgsql;