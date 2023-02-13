ANALYTICS_DB = "client_api_analytics_{env}"
EVP_DB = "client_api_evp_{env}"
TSP_DB = "client_api_tsp_{env}"

CVP_TABLES = [
    # TSP
    {
        "external_db": TSP_DB,
        "table": "cvp_vehicle_logs",
    },
    # Metrics
    {
        "dag": "metrics-lateness",
        "external_schema": "ext_tsp",
        "schema": "public",
        "table": "lateness_source_data",
        "path": "lateness/lateness_source_data",
    },
    # Intersections
    {
        "dag": "metrics-route-to-intersection",
        "external_schema": "ext_tsp",
        "schema": "public",
        "table": "route_to_intersection_mapping",
        "path": "route_to_intersection/route_to_intersection_mapping",
    },
    {
        "dag": "tsp-dataset",
        "external_schema": "ext_tsp",
        "schema": "public",
        "table": "intersection_status_report",
        "path": "tsp_source_data/tsp_dataset/intersection_status_report",
    },
]

RT_GTFS_TABLE = {
    "external_db": TSP_DB,
    "table": "rt_gtfs_vehicle_positions",
}

RT_RADIO_TABLE = {
    "external_db": ANALYTICS_DB,
    "table": "rt_radio_messages",
}

MP70_TABLES = [
    {
        "external_db": EVP_DB,
        "table": "devices",
    },
    {
        "external_db": EVP_DB,
        "table": "intersections",
    },
    {
        "external_db": ANALYTICS_DB,
        "table": "mp70",
    },
]

GTFS_TABLES = [
    {
        "dag": "gtfs-dataset",
        "external_schema": "ext_gtfs",
        "schema": "gtfs",
        "table": "agency",
        "path": "gtfs/agency",
    },
    {
        "dag": "gtfs-dataset",
        "external_schema": "ext_gtfs",
        "schema": "gtfs",
        "table": "routes",
        "path": "gtfs/routes",
    },
    {
        "dag": "gtfs-dataset",
        "external_schema": "ext_gtfs",
        "schema": "gtfs",
        "table": "shapes",
        "path": "gtfs/shapes",
    },
    {
        "dag": "gtfs-dataset",
        "external_schema": "ext_gtfs",
        "schema": "gtfs",
        "table": "stop_times",
        "path": "gtfs/stop_times",
    },
    {
        "dag": "gtfs-dataset",
        "external_schema": "ext_gtfs",
        "schema": "gtfs",
        "table": "stops",
        "path": "gtfs/stops",
    },
    {
        "dag": "gtfs-dataset",
        "external_schema": "ext_gtfs",
        "schema": "gtfs",
        "table": "trips",
        "path": "gtfs/trips",
    },
]
