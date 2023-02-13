CREATE OR REPLACE PROCEDURE sp_assert (
  p_predicate BOOL,
  p_message TEXT
)
AS $$
BEGIN
  IF NOT p_predicate
  THEN
    RAISE EXCEPTION '%', p_message;
  END IF;
END;
$$ LANGUAGE plpgsql;