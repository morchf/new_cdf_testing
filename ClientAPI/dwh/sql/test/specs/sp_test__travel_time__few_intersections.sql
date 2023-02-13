CREATE
OR REPLACE PROCEDURE testing.sp_test__travel_time__few_intersections () AS $$ BEGIN
  -- Mock source tables
  CALL testing.sp_fixture__travel_time__few_intersections();

CALL sp_vehicle_positions();

CALL sp_intersection_positions();

CALL sp_segment_events();

CALL testing.sp_mock_table(
  'segment_events',
  'AS SELECT * FROM staging__segment_events'
);

END;

$$ LANGUAGE plpgsql;