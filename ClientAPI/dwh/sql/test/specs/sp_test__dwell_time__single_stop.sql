CREATE
OR REPLACE PROCEDURE testing.sp_test__dwell_time__single_stop () AS $$
DECLARE
  l_value FLOAT;

l_epsilon FLOAT;

BEGIN
  l_epsilon := 0.0001;

-- Mock source tables
CALL testing.sp_fixture__dwell_time__single_stop();

CALL sp_vehicle_positions();

CALL sp_intersection_positions();

CALL sp_segment_events();

CALL testing.sp_mock_table(
  'segment_events',
  'AS SELECT * FROM staging__segment_events'
);

-- Mock materialized views
CALL testing.sp_mock_mv('mv_dwell_time');

CALL testing.sp_mock_mv('mv_signal_delay');

CALL testing.sp_mock_mv('mv_drive_time');

CALL testing.sp_mock_mv('mv_travel_time');

-- Test
SELECT
  INTO l_value dwell_time
FROM
  mv_dwell_time
WHERE
  trip_start_time = '2022-03-14 18:46:58.126' :: TIMESTAMP;

CALL sp_assert(ABS(l_value - 17.358) < l_epsilon);

END;

$$ LANGUAGE plpgsql;