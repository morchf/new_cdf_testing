CREATE OR REPLACE
FUNCTION f_at (
  SUPER, -- Array of text elements
  INT    -- Index of element
) RETURNS TEXT -- Element at index
STABLE
AS $$
	SELECT
		JSON_EXTRACT_ARRAY_ELEMENT_TEXT(
			JSON_SERIALIZE($1),
      $2
    )
$$ LANGUAGE SQL;
