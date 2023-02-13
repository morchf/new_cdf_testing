-- Populate GTFS tables
CALL sp_copy_external('ext_gtfs.agency', 'gtfs.agency');
CALL sp_copy_external('ext_gtfs.routes', 'gtfs.routes');
CALL sp_copy_external('ext_gtfs.shapes', 'gtfs.shapes');
CALL sp_copy_external('ext_gtfs.stop_times', 'gtfs.stop_times');
CALL sp_copy_external('ext_gtfs.stops', 'gtfs.stops');
CALL sp_copy_external('ext_gtfs.trips', 'gtfs.trips');
-- Populate metrics tables
CALL sp_copy_external(
  'ext_tsp.lateness_source_data',
  'public.lateness_source_data'
);
CALL sp_copy_external(
  'ext_tsp.intersection_status_report',
  'public.intersection_status_report'
);
CALL sp_copy_external(
  'ext_tsp.route_to_intersection_mapping',
  'public.route_to_intersection_mapping'
);