CREATE
OR REPLACE PROCEDURE sp_parse_vehicle_logs (
  -- Procedure to handle log parsing. E.g. sp_segment_events
  p_procedure TEXT,
  -- Table partitions. I.e "agency": ["sfmta"], "date": ["2021-09-02"]
  p_partitions SUPER
) AS $$
DECLARE
  l_record RECORD;

-- Agency/date pairs
l_agencies SUPER;

l_dates SUPER;

BEGIN
  l_agencies := JSON_PARSE(
    JSON_EXTRACT_PATH_TEXT(JSON_SERIALIZE(p_partitions), 'agency')
  );

l_dates := JSON_PARSE(
  JSON_EXTRACT_PATH_TEXT(JSON_SERIALIZE(p_partitions), 'date')
);

RAISE INFO 'Looping through each agency/date, starting with the newest date';

FOR l_record IN (
  SELECT
    agency,
    "date"
  FROM
    log_dates
  WHERE
    (
      l_agencies IS NULL
      OR f_contains(l_agencies, agency)
    )
    AND (
      l_dates IS NULL
      OR f_contains(l_dates, "date")
    )
  ORDER BY
    "date" DESC
)
LOOP
  EXECUTE 'CALL ' || p_procedure || ' (' || QUOTE_LITERAL(l_record.agency) || '::TEXT,' || QUOTE_LITERAL(l_record.date) || '::TEXT)';

END
LOOP
;

RAISE INFO 'Parsed vehicle logs';

END;

$$ LANGUAGE plpgsql;