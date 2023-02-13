CREATE OR REPLACE PROCEDURE sp_assert (
  p_predicate BOOL
)
AS $$
BEGIN
  CALL sp_assert(p_predicate, 'Assertion error');
END;
$$ LANGUAGE plpgsql;