"""
Execute SQL files in the below direction/file order

Must define scripts with dependencies on other SQL resources to execute after
the dependency

E.g. Views depending on a table, functions depending on other functions
"""

SQL_FILES = [
    "functions/f_progress.sql",
    "functions",
    "test/pre.sql",
    "scripts/pre",
    "procedures/sp_drop_procedure.sql",
    "procedures",
    "tables",
    "views/tsp/mv_intersections.sql",
    "views/tsp/mv_intersection_dates.sql",
    "views/tsp/mv_gtfs_dates.sql",
    "views/tsp/mv_gtfs_stops.sql",
    "views/tsp/mv_gtfs_segments.sql",
    "views/tsp/mv_dwell_time.sql",
    "views/tsp/mv_signal_delay.sql",
    "views/tsp/v_signal_delay.sql",
    "views/tsp/mv_drive_time.sql",
    "views/tsp/mv_travel_time.sql",
    "views/tsp/mv_availability.sql",
    "views/evp/mv_evp_dates.sql",
    "views/evp/mv_evp_corridors.sql",
    "views",
    # Testing
    "test/fixtures",
    "test/specs",
    "test/post.sql",
    "scripts/post",
]
