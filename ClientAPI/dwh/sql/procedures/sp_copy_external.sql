CREATE OR REPLACE PROCEDURE sp_copy_external (
  p_external_table TEXT,
  p_table TEXT,
  p_partitions SUPER
)
AS $$
DECLARE
  -- Table params
  l_external_schema TEXT;
  l_external_table TEXT;

  l_schema TEXT;
  l_table TEXT;

  -- SQL predicate
  l_sql VARCHAR(6000);

  -- Columns and partitions
  l_partition SUPER;
  l_partition_key TEXT;
  l_partition_values SUPER;
  l_partition_value TEXT;
BEGIN
  l_external_schema = f_at(SPLIT_TO_ARRAY(p_table, '.'), 0);
  l_external_table = f_at(SPLIT_TO_ARRAY(p_table, '.'), 1);
  
  l_schema = f_at(SPLIT_TO_ARRAY(p_table, '.'), 0);
  l_table = f_at(SPLIT_TO_ARRAY(p_table, '.'), 1);

  -- For each partition key-value pair
  -- Construct dynamic 'IN' predicate
  -- e.g. [['p1',['v1','v2],['p2',['v3']]] -> p1 IN ('v1','v2') AND p2 in ('v3')
  l_sql := '';
  IF p_partitions IS NOT NULL
  THEN
    FOR i IN 0..(GET_ARRAY_LENGTH(p_partitions) - 1)
    LOOP 
      l_partition := JSON_PARSE(f_at(p_partitions, i));
      l_partition_key := f_at(l_partition, 0);
      l_partition_values := JSON_PARSE(f_at(l_partition, 1));

      l_sql := l_sql || l_partition_key || '::VARCHAR IN (';

      FOR j IN 0..(GET_ARRAY_LENGTH(l_partition_values) - 1)
      LOOP
        l_partition_value := f_at(l_partition_values, j);
        l_sql := l_sql || QUOTE_LITERAL(l_partition_value) || ',';
      END LOOP;

      l_sql := TRIM(l_sql, ',');
      l_sql := l_sql || ') AND ';
    END LOOP;
    l_sql := TRIM(l_sql, ' AND ');
  ELSE
    -- Default to all records
    l_sql = 'TRUE';
  END IF;

  -- Delete existing
  EXECUTE  'DELETE FROM ' || p_table ||
    ' WHERE ' || l_sql;

  RAISE INFO 'Removed existing';

  -- Copy from external
   EXECUTE 'INSERT INTO ' || p_table ||
     ' SELECT * FROM ' || p_external_table ||
     ' WHERE ' || l_sql;

  RAISE INFO 'Copied to DWH';

END;
$$ LANGUAGE plpgsql;
