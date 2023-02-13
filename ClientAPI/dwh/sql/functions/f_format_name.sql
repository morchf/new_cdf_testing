/*
 Remove unnecessay characters from unique name

 Args:
 VARCHAR Name
 
 Returns: Name with unused characters removed
 */
CREATE
OR REPLACE FUNCTION f_format_name (VARCHAR) RETURNS VARCHAR STABLE AS $$
SELECT
  REPLACE($1, ':', '') $$ LANGUAGE SQL