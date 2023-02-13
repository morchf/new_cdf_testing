CREATE
OR REPLACE PROCEDURE testing.sp_test__travel_time () AS $$ BEGIN
  -- Mock source tables
  CALL testing.sp_fixture__travel_time();

CALL sp_vehicle_positions();

CALL sp_intersection_positions();

CALL sp_segment_events();

CALL testing.sp_mock_table(
  'segment_events',
  'AS SELECT * FROM staging__segment_events'
);

-- Mock views
CALL testing.sp_mock_mv('mv_dwell_time');

CALL testing.sp_mock_mv('mv_drive_time');

CALL testing.sp_mock_mv('mv_signal_delay');

CALL testing.sp_mock_mv('mv_travel_time');

-- Test
-- TODO
END;

$$ LANGUAGE plpgsql;