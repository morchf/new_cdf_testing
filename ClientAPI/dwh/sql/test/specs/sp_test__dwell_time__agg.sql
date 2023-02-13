CREATE
OR REPLACE PROCEDURE testing.sp_test__dwell_time__agg () AS $$
DECLARE
  l_value FLOAT;

l_epsilon FLOAT;

BEGIN
  l_epsilon := 0.0001;

-- Mock source tables
CALL testing.sp_fixture__dwell_time__single_stop();

CALL sp_vehicle_positions__cvp();

CALL sp_intersection_positions__cvp();

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
END;

$$ LANGUAGE plpgsql;