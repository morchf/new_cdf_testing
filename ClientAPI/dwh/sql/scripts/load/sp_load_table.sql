CREATE OR REPLACE PROCEDURE sp_load_table (
  p_s3_bucket TEXT,
  p_src_schema_name TEXT,
  p_src_table_name TEXT,
  p_dest_schema_name TEXT,
  p_dest_table_name TEXT
)
  AS $$
DECLARE
  l_iam_role text;
  l_record RECORD;
BEGIN
  SELECT
    REPLACE(REPLACE(es.esoptions, '{"IAM_ROLE":"', ''), '"}', '') INTO l_iam_role FROM svv_external_schemas es LIMIT 1;

    RAISE INFO 'Loading %.%', p_src_schema_name, p_src_table_name;
    EXECUTE 'COPY ' || p_dest_schema_name || '.' || p_dest_table_name
    -- Unload to ETL bucket, partitioned by schema/table
    || ' FROM ' || QUOTE_LITERAL(p_s3_bucket || '/unload/' || p_src_schema_name || '/' || p_src_table_name)
    -- Use primary role
    || ' IAM_ROLE ' || QUOTE_LITERAL(l_iam_role)
    || ' MAXERROR 10000';
END;
$$
LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE sp_load_table (
  p_s3_bucket TEXT,
  p_src_schema_name TEXT,
  p_src_table_name TEXT
)
  AS $$
DECLARE
  l_iam_role text;
  l_record RECORD;
BEGIN
  CALL sp_load_table(p_s3_bucket, p_src_schema_name, p_src_table_name, p_src_schema_name, p_src_table_name);
END;
$$
LANGUAGE plpgsql;


/**
CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'agency')
 */
