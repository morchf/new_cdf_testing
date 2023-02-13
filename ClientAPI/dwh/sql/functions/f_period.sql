/*
 Convert a VARCHAR in a DATE format to the first date in the selected period
 
 Args:
 VARCHAR Selected period
 VARCHAR Date
 
 Returns: VARCHAR of the first date in the selected period
 */
CREATE
OR REPLACE FUNCTION f_period (VARCHAR, VARCHAR) RETURNS VARCHAR STABLE AS $$
SELECT
  TO_CHAR(DATE_TRUNC($1, $2 :: DATE), 'YYYY-MM-DD') $$ LANGUAGE SQL