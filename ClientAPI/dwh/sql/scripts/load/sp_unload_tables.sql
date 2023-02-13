CREATE OR REPLACE PROCEDURE sp_unload_tables (p_s3_bucket text)
  AS $$
DECLARE
  l_iam_role text;
  l_record RECORD;
BEGIN
  SELECT
    REPLACE(REPLACE(es.esoptions, '{"IAM_ROLE":"', ''), '"}', '') INTO l_iam_role FROM svv_external_schemas es LIMIT 1;
  -- Unload each table
  FOR l_record IN ( SELECT DISTINCT
      schemaname,
      tablename
    FROM
      pg_tables
    WHERE
      tableowner <> 'rdsdb'
      AND schemaname <> 'pg_temp_2'
    ORDER BY
      schemaname,
      tablename)
    LOOP
      RAISE INFO 'Unloading %.%', l_record.schemaname, l_record.tablename;
      EXECUTE 'UNLOAD (' || QUOTE_LITERAL('SELECT * FROM ' || l_record.schemaname || '.' || l_record.tablename) || ')'
      -- Unload to ETL bucket, partitioned by schema/table
      || ' TO ' || QUOTE_LITERAL(p_s3_bucket || '/unload/' || l_record.schemaname || '/' || l_record.tablename || '/' || l_record.tablename || '_')
      -- Use primary role
      || ' IAM_ROLE ' || QUOTE_LITERAL(l_iam_role);
    END LOOP;
END;
$$
LANGUAGE plpgsql;


/**
CALL sp_unload_tables('s3://client-api-etl-develop')
 */
