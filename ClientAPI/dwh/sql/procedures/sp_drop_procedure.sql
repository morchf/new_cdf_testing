CREATE OR REPLACE PROCEDURE sp_drop_procedure (
  p_schema_name VARCHAR,
  p_proc_name VARCHAR
)
AS $$
DECLARE
  l_record RECORD;
  l_arg_name TEXT;
  l_arg_type TEXT;
	l_signature TEXT;
BEGIN

  FOR l_record IN (
    SELECT * FROM PG_PROC_INFO
    WHERE proname = p_proc_name
  ) LOOP

	  l_signature := p_schema_name || '.' || p_proc_name || '(';

    -- Loop through all matching procedures
    FOR i IN 0..(l_record.pronargs - 1)
    LOOP
      -- Convert name 'text[]' to 'string'
      SELECT l_record.proargnames INTO l_arg_name;
      l_arg_name := TRIM('}' FROM TRIM('{' FROM l_arg_name));
      EXECUTE 'SELECT names[' || i || ']::VARCHAR
        FROM (
          SELECT (
            split_to_array(' || QUOTE_LITERAL(l_arg_name) || ', \',\')
          ) AS names
        )' INTO l_arg_name;

      -- Convert type 'text[]' to 'string'
      SELECT l_record.proallargtypes INTO l_arg_type;
      l_arg_type := TRIM('}' FROM TRIM('{' FROM l_arg_type));
      EXECUTE 'SELECT types[' || i || ']::VARCHAR
      FROM (
        SELECT (
          split_to_array(' || QUOTE_LITERAL(l_arg_type) || ', \',\')
        ) AS types
      )' INTO l_arg_type;

      -- Match type ID to type name
      EXECUTE 'SELECT TRIM(\'_\' FROM typname)
        FROM pg_type
        WHERE typelem = ' || QUOTE_LITERAL(l_arg_type) INTO l_arg_type;

      -- Add arg name and type
      l_signature := l_signature || l_arg_name || ' ' || l_arg_type || ',';

    END LOOP;

	l_signature := TRIM(',' FROM l_signature) || ')';

  -- Drop procedure with matching name
	EXECUTE 'DROP PROCEDURE '|| l_signature;

  END LOOP;
END;
$$ LANGUAGE plpgsql;
