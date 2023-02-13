CREATE OR REPLACE FUNCTION
f_folder (
  file_name TEXT,
  FOLDER_NAME VARCHAR
)
RETURNS VARCHAR
STABLE
AS $$
  SELECT REGEXP_SUBSTR(
    $1,
    REPLACE('%s=([^\/]*)', '%s', $2),
    1, 1, 'e'
  )
$$ LANGUAGE SQL;
