CREATE OR REPLACE
PROCEDURE sp_routes_map_data(
	p_agency IN VARCHAR,
	p_route IN VARCHAR,
	p_start_date IN DATE,
	p_end_date IN DATE,
	p_selected_direction IN SUPER,
	o INOUT refcursor
)
AS $$
BEGIN
	OPEN o FOR
	WITH timeframe AS (
	  SELECT
	    MAX(
	      CASE
	        WHEN "date" <= p_start_date then "date"
	      END
	    ) AS start_date,
	    MAX(
	      CASE
	        WHEN "date" <= p_end_date then "date"
	      END
	    ) AS end_date
	  FROM public.agency
	  WHERE agency = p_agency
	)
	SELECT
	  *
	FROM
	  gtfs.mv_routes_map_data
	WHERE
	  agency = p_agency
	  AND route = p_route
	  AND "date" BETWEEN (SELECT start_date FROM timeframe)
	  AND (SELECT end_date FROM timeframe)
	  AND f_contains(p_selected_direction, direction)
	ORDER BY
	  "date" DESC,
	  route,
	  shape_id;
 END;
$$ LANGUAGE plpgsql;