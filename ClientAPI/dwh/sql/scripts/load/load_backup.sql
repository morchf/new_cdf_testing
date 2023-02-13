CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'agency');
CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'routes');
CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'shapes');
CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'stop_times');
CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'stops');
CALL sp_load_table('s3://client-api-etl-develop', 'gtfs', 'trips');

CALL sp_load_table('s3://client-api-etl-develop', 'evp', 'evp_corridors');
CALL sp_load_table('s3://client-api-etl-develop', 'evp', 'evp_devices');
CALL sp_load_table('s3://client-api-etl-develop', 'evp', 'evp_incidents');
CALL sp_load_table('s3://client-api-etl-develop', 'evp', 'evp_intersections');

CALL sp_load_table('s3://client-api-etl-develop', 'assets', 'intersections');

CALL sp_load_table('s3://client-api-etl-develop', 'public', 'cfg_agency');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'evp_events');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'intersection_events');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'intersection_status_report');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'lateness_source_data');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'log_dates');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'route_to_intersection_mapping');
CALL sp_load_table('s3://client-api-etl-develop', 'public', 'segment_events');


-- Refresh procedures

CALL sp_refresh_gtfs();
CALL sp_refresh_travel_time();
CALL sp_refresh_tsp();