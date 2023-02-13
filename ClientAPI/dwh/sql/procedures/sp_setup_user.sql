CREATE OR REPLACE PROCEDURE sp_setup_user (
  p_database TEXT,
  p_name TEXT,
  p_password TEXT,
  p_tables SUPER
)
AS $$
DECLARE
  l_record RECORD;
   l_exists BOOL;
BEGIN
  -- Hold schemas/tables
  DROP TABLE IF EXISTS sp_setup_user__tables;
  CREATE TEMP TABLE sp_setup_user__tables
  AS
    SELECT p_tables AS items;
  
  DROP TABLE IF EXISTS sp_setup_user__schema_tables;
  CREATE TEMP TABLE sp_setup_user__schema_tables
  AS
    WITH exploded AS (
      SELECT items as item
      FROM sp_setup_user__tables AS t
      LEFT JOIN t.items AS items ON TRUE
    )
    SELECT
      SPLIT_PART(item::TEXT, '.', 1) AS schema,
        SPLIT_PART(item::TEXT, '.', 2) AS table
    FROM exploded;

  -- Check for existing users
  SELECT INTO l_exists COUNT(*)::BOOL
  FROM pg_user
  WHERE usename = p_name;

  EXECUTE 'REVOKE ASSUMEROLE ON ALL FROM PUBLIC FOR ALL';

  /*
    Remove user permissions if existing user
  */
  IF l_exists THEN
    FOR l_record IN (
      SELECT DISTINCT schemaname
      FROM pg_tables
      WHERE
        tableowner <> 'rdsdb'
        AND schemaname <> 'pg_temp_2'
      UNION
      select nspname as schemaname
      from pg_namespace a,
      pg_external_schema b where a.oid=b.esoid
    )
      LOOP
        RAISE INFO 'Revoke on schema %', l_record.schemaname;
        EXECUTE 'REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA 
          ' || l_record.schemaname || ' FROM ' || p_name;
        EXECUTE 'REVOKE EXECUTE ON ALL PROCEDURES IN SCHEMA 
          ' || l_record.schemaname || ' FROM ' || p_name;
        EXECUTE 'REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA
          ' || l_record.schemaname || ' FROM ' || p_name;
        EXECUTE 'REVOKE ALL PRIVILEGES ON SCHEMA 
          ' || l_record.schemaname || ' FROM ' || p_name;
        EXECUTE 'REVOKE ALL ON  SCHEMA 
          ' || l_record.schemaname || ' FROM ' || p_name;
    END LOOP;

    EXECUTE 'REVOKE ALL PRIVILEGES ON DATABASE ' || p_database  || ' FROM ' || p_name;
    EXECUTE 'REVOKE ASSUMEROLE ON 
        ' || QUOTE_LITERAL('{IAM_ROLE}') || ' FROM 
        ' || p_name || ' FOR ALL';
  END IF;
  
  /*
    Create user
  */
  EXECUTE 'DROP USER IF EXISTS ' || p_name;
  EXECUTE 'CREATE USER ' || p_name || ' PASSWORD ' || QUOTE_LITERAL(p_password);
  EXECUTE 'GRANT ASSUMEROLE ON ' || QUOTE_LITERAL('{IAM_ROLE}') || ' TO ' || p_name || ' FOR ALL';

  /*
    Add permissions
  */
  -- Remove implicit 'Create' permissions  on 'public' schema
  EXECUTE 'REVOKE CREATE ON SCHEMA public FROM ' || p_name;

  -- Add schema permissions
  FOR l_record IN (SELECT DISTINCT "schema" FROM sp_setup_user__schema_tables)
  LOOP
    EXECUTE 'GRANT USAGE ON SCHEMA  
      ' || l_record.schema || ' TO ' || p_name;
    EXECUTE 'GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA  
      ' || l_record.schema || ' TO ' || p_name;
    EXECUTE 'GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA
      ' || l_record.schema || ' TO ' || p_name;
  END LOOP;

  -- Add table permissions
  FOR l_record IN (SELECT * FROM sp_setup_user__schema_tables)
  LOOP
    IF NOT l_record.table = '' THEN
      EXECUTE 'GRANT SELECT ON  
        ' || l_record.schema || '.' || l_record.table || ' TO ' || p_name;
    END IF;
    IF l_record.table = '' THEN
      EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA 
        ' || l_record.schema || ' TO ' || p_name;
    END IF;
  END LOOP;
END;
$$ LANGUAGE plpgsql;