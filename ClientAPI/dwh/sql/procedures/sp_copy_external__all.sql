CREATE OR REPLACE PROCEDURE sp_copy_external (
  p_external_table TEXT,
  p_table TEXT
)
AS $$
BEGIN
  CALL sp_copy_external(p_external_table, p_table, NULL::SUPER);
END;
$$ LANGUAGE plpgsql;
