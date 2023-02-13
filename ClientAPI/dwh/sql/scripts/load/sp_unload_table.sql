CREATE OR REPLACE PROCEDURE sp_unload_table (
  p_s3_bucket TEXT,
  p_schema_name TEXT,
  p_table_name TEXT
)
  AS $$
DECLARE
  l_iam_role text;
  l_record RECORD;
BEGIN
  SELECT
    REPLACE(REPLACE(es.esoptions, '{"IAM_ROLE":"', ''), '"}', '') INTO l_iam_role FROM svv_external_schemas es LIMIT 1;
    RAISE INFO 'Unloading %.%', p_schema_name, p_table_name;
    EXECUTE 'UNLOAD (' || QUOTE_LITERAL('SELECT * FROM ' || p_schema_name || '.' || p_table_name) || ')'
    -- Unload to ETL bucket, partitioned by schema/table
    || ' TO ' || QUOTE_LITERAL(p_s3_bucket || '/unload/' || p_schema_name || '/' || p_table_name || '/' || p_table_name || '_')
    -- Use primary role
    || ' IAM_ROLE ' || QUOTE_LITERAL(l_iam_role);
END;
$$
LANGUAGE plpgsql;


/**
CALL sp_unload_table('s3://client-api-etl-develop', 'public', 'lateness_source_data')
 */
