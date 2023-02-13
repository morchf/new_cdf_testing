CREATE OR REPLACE PROCEDURE sp_parse_vehicle_logs__all (
  -- Procedure to handle log parsing. E.g. sp_parse_vehicle_logs__cvp
  p_procedure TEXT
)
AS $$
DECLARE
  l_record RECORD;
BEGIN
  CALL sp_parse_vehicle_logs(p_procedure, JSON_PARSE('{}'));
END;
$$ LANGUAGE plpgsql;
