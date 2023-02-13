CREATE OR REPLACE
PROCEDURE sp_routes_availability_period(
	p_agency IN VARCHAR,
	p_start_date IN DATE,
	p_end_date IN DATE,
	o INOUT refcursor
)
AS $$
BEGIN
	OPEN o FOR
  WITH date_range AS (
    SELECT MAX(
      CASE
        WHEN "date" <= p_start_date then "date"
      END
    ) AS start_date,
    MAX(
      CASE
        WHEN "date" <= p_end_date then "date"
      END
    ) AS end_date
  FROM
    gtfs.agency
  WHERE
    agency = p_agency
  )
  SELECT
    COALESCE(start_date, end_date) AS start_date,
    COALESCE(end_date, start_date) AS end_date
  FROM date_range;
END;
$$ LANGUAGE plpgsql;