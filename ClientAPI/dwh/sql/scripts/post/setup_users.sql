/*
 Create users
 */
-- Admin user available under 'awsuser'
-- User for API
CALL sp_setup_user(
  '{ENV}',
  'api',
  '{API_USER_SECRET}',
  ARRAY(
    'gtfs.agency',
    'gtfs.routes',
    'gtfs.shapes',
    'gtfs.stop_times',
    'gtfs.stops',
    'gtfs.trips',
    'gtfs.mv_routes_map_data',
    'public.lateness_source_data',
    'public.mv_travel_time',
    'public.v_signal_delay',
    'public.route_to_intersection_mapping',
    'public.intersection_status_report',
    'public.mv_availability',
    'public.mv_intersections'
  )
);

-- EVP user
CALL sp_setup_user(
  '{ENV}',
  'evp',
  '{EVP_USER_SECRET}',
  ARRAY(
    'public.evp_events',
    'public.mv_evp_corridors',
    'public.mv_evp_corridor_trips',
    'public.mv_evp_dates',
    'public.mv_evp_routes',
    'evp'
  )
);
-- Grant procedure/function permissions
GRANT ALL ON ALL PROCEDURES IN SCHEMA public TO PUBLIC;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO PUBLIC;