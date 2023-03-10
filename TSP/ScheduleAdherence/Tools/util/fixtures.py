from pydantic import parse_obj_as
from util.scenarios import ScenarioDefinition, from_breadcrumbs, from_file

STOPS_BASIC = [
    {
        "stop_id": "7765",
        "stop_lat": 37.771146,
        "stop_lon": -122.389936,
    },
    {
        "stop_id": "7766",
        "stop_lat": 37.770513,
        "stop_lon": -122.391037,
    },
    {
        "stop_id": "7324",
        "stop_lat": 37.76871,
        "stop_lon": -122.389377,
    },
    {
        "stop_id": "7767",
        "stop_lat": 37.766864,
        "stop_lon": -122.390891,
    },
    {
        "stop_id": "7865",
        "stop_lat": 37.766722,
        "stop_lon": -122.392805,
    },
    {
        "stop_id": "7768",
        "stop_lat": 37.766492,
        "stop_lon": -122.397011,
    },
    {
        "stop_id": "7769",
        "stop_lat": 37.766287,
        "stop_lon": -122.399842,
    },
    {
        "stop_id": "7770",
        "stop_lat": 37.76611,
        "stop_lon": -122.402822,
    },
    {
        "stop_id": "3302",
        "stop_lat": 37.766039,
        "stop_lon": -122.40469,
    },
    {
        "stop_id": "3295",
        "stop_lat": 37.7658,
        "stop_lon": -122.407624,
    },
    {
        "stop_id": "3281",
        "stop_lat": 37.765658,
        "stop_lon": -122.410294,
    },
    {
        "stop_id": "3288",
        "stop_lat": 37.765523,
        "stop_lon": -122.412976,
    },
    {
        "stop_id": "7289",
        "stop_lat": 37.7654,
        "stop_lon": -122.415428,
    },
    {
        "stop_id": "3291",
        "stop_lat": 37.765152,
        "stop_lon": -122.419611,
    },
    {
        "stop_id": "3300",
        "stop_lat": 37.764987,
        "stop_lon": -122.421746,
    },
    {
        "stop_id": "3286",
        "stop_lat": 37.764853,
        "stop_lon": -122.423959,
    },
    {
        "stop_id": "3284",
        "stop_lat": 37.764731,
        "stop_lon": -122.426156,
    },
    {
        "stop_id": "3283",
        "stop_lat": 37.764579,
        "stop_lon": -122.428523,
    },
    {
        "stop_id": "7073",
        "stop_lat": 37.767509,
        "stop_lon": -122.428927,
    },
    {
        "stop_id": "4006",
        "stop_lat": 37.769302,
        "stop_lon": -122.429087,
    },
    {
        "stop_id": "5017",
        "stop_lat": 37.770307,
        "stop_lon": -122.429929,
    },
    {
        "stop_id": "4620",
        "stop_lat": 37.772033,
        "stop_lon": -122.430347,
    },
    {
        "stop_id": "4631",
        "stop_lat": 37.774268,
        "stop_lon": -122.430825,
    },
    {
        "stop_id": "4621",
        "stop_lat": 37.776106,
        "stop_lon": -122.431197,
    },
    {
        "stop_id": "4616",
        "stop_lat": 37.776998,
        "stop_lon": -122.431369,
    },
    {
        "stop_id": "4628",
        "stop_lat": 37.77854,
        "stop_lon": -122.431687,
    },
    {
        "stop_id": "4613",
        "stop_lat": 37.779859,
        "stop_lon": -122.431955,
    },
    {
        "stop_id": "4611",
        "stop_lat": 37.781733,
        "stop_lon": -122.432329,
    },
    {
        "stop_id": "4633",
        "stop_lat": 37.783193,
        "stop_lon": -122.432627,
    },
    {
        "stop_id": "4614",
        "stop_lat": 37.784733,
        "stop_lon": -122.432921,
    },
    {
        "stop_id": "4640",
        "stop_lat": 37.786051,
        "stop_lon": -122.433244,
    },
    {
        "stop_id": "4635",
        "stop_lat": 37.788049,
        "stop_lon": -122.433565,
    },
    {
        "stop_id": "4638",
        "stop_lat": 37.789744,
        "stop_lon": -122.433947,
    },
    {
        "stop_id": "4623",
        "stop_lat": 37.792761,
        "stop_lon": -122.434556,
    },
    {
        "stop_id": "4604",
        "stop_lat": 37.794158,
        "stop_lon": -122.434842,
    },
    {
        "stop_id": "3085",
        "stop_lat": 37.794131,
        "stop_lon": -122.436442,
    },
    {
        "stop_id": "6492",
        "stop_lat": 37.794911,
        "stop_lon": -122.436669,
    },
    {
        "stop_id": "6487",
        "stop_lat": 37.795859,
        "stop_lon": -122.436863,
    },
    {
        "stop_id": "6490",
        "stop_lat": 37.796785,
        "stop_lon": -122.437054,
    },
    {
        "stop_id": "4643",
        "stop_lat": 37.797391,
        "stop_lon": -122.435489,
    },
    {
        "stop_id": "4626",
        "stop_lat": 37.799707,
        "stop_lon": -122.435952,
    },
    {
        "stop_id": "4608",
        "stop_lat": 37.801091,
        "stop_lon": -122.436229,
    },
    {
        "stop_id": "4603",
        "stop_lat": 37.802585,
        "stop_lon": -122.43668,
    },
]

SCHEDULE_STATUS_BASIC = {
    "trip_id": "10536292",
    "vehicle_id": "ve",
    "delay": 20,
    "stop_events": [{"stop_id": "7765", "timestamp": "2022-10-30 09:18:40"}],
}

STOP_TIMES_BASIC = [
    {
        "trip_id": "10536292",
        "stop_id": "7765",
        "stop_sequence": 1,
        "arrival_time": "09:19:00",
        "departure_time": "09:19:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7766",
        "stop_sequence": 2,
        "arrival_time": "09:19:34",
        "departure_time": "09:19:34",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7324",
        "stop_sequence": 3,
        "arrival_time": "09:20:40",
        "departure_time": "09:20:40",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7767",
        "stop_sequence": 4,
        "arrival_time": "09:21:59",
        "departure_time": "09:21:59",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7865",
        "stop_sequence": 5,
        "arrival_time": "09:22:33",
        "departure_time": "09:22:33",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7768",
        "stop_sequence": 6,
        "arrival_time": "09:23:48",
        "departure_time": "09:23:48",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7769",
        "stop_sequence": 7,
        "arrival_time": "09:24:38",
        "departure_time": "09:24:38",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7770",
        "stop_sequence": 8,
        "arrival_time": "09:25:31",
        "departure_time": "09:25:31",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3302",
        "stop_sequence": 9,
        "arrival_time": "09:26:04",
        "departure_time": "09:26:04",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3295",
        "stop_sequence": 10,
        "arrival_time": "09:27:00",
        "departure_time": "09:27:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3281",
        "stop_sequence": 11,
        "arrival_time": "09:28:00",
        "departure_time": "09:28:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3288",
        "stop_sequence": 12,
        "arrival_time": "09:29:09",
        "departure_time": "09:29:09",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7289",
        "stop_sequence": 13,
        "arrival_time": "09:30:11",
        "departure_time": "09:30:11",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3291",
        "stop_sequence": 14,
        "arrival_time": "09:32:00",
        "departure_time": "09:32:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3300",
        "stop_sequence": 15,
        "arrival_time": "09:32:59",
        "departure_time": "09:32:59",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3286",
        "stop_sequence": 16,
        "arrival_time": "09:34:00",
        "departure_time": "09:34:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3284",
        "stop_sequence": 17,
        "arrival_time": "09:35:01",
        "departure_time": "09:35:01",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3283",
        "stop_sequence": 18,
        "arrival_time": "09:36:06",
        "departure_time": "09:36:06",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "7073",
        "stop_sequence": 19,
        "arrival_time": "09:38:00",
        "departure_time": "09:38:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4006",
        "stop_sequence": 20,
        "arrival_time": "09:39:01",
        "departure_time": "09:39:01",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "5017",
        "stop_sequence": 21,
        "arrival_time": "09:39:55",
        "departure_time": "09:39:55",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4620",
        "stop_sequence": 22,
        "arrival_time": "09:41:00",
        "departure_time": "09:41:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4631",
        "stop_sequence": 23,
        "arrival_time": "09:42:43",
        "departure_time": "09:42:43",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4621",
        "stop_sequence": 24,
        "arrival_time": "09:44:07",
        "departure_time": "09:44:07",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4616",
        "stop_sequence": 25,
        "arrival_time": "09:44:48",
        "departure_time": "09:44:48",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4628",
        "stop_sequence": 26,
        "arrival_time": "09:46:00",
        "departure_time": "09:46:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4613",
        "stop_sequence": 27,
        "arrival_time": "09:46:52",
        "departure_time": "09:46:52",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4611",
        "stop_sequence": 28,
        "arrival_time": "09:48:06",
        "departure_time": "09:48:06",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4633",
        "stop_sequence": 29,
        "arrival_time": "09:49:04",
        "departure_time": "09:49:04",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4614",
        "stop_sequence": 30,
        "arrival_time": "09:50:05",
        "departure_time": "09:50:05",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4640",
        "stop_sequence": 31,
        "arrival_time": "09:51:00",
        "departure_time": "09:51:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4635",
        "stop_sequence": 32,
        "arrival_time": "09:52:08",
        "departure_time": "09:52:08",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4638",
        "stop_sequence": 33,
        "arrival_time": "09:53:06",
        "departure_time": "09:53:06",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4623",
        "stop_sequence": 34,
        "arrival_time": "09:54:49",
        "departure_time": "09:54:49",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4604",
        "stop_sequence": 35,
        "arrival_time": "09:55:37",
        "departure_time": "09:55:37",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "3085",
        "stop_sequence": 36,
        "arrival_time": "09:56:21",
        "departure_time": "09:56:21",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "6492",
        "stop_sequence": 37,
        "arrival_time": "09:56:53",
        "departure_time": "09:56:53",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "6487",
        "stop_sequence": 38,
        "arrival_time": "09:57:25",
        "departure_time": "09:57:25",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "6490",
        "stop_sequence": 39,
        "arrival_time": "09:58:00",
        "departure_time": "09:58:00",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4643",
        "stop_sequence": 40,
        "arrival_time": "09:59:11",
        "departure_time": "09:59:11",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4626",
        "stop_sequence": 41,
        "arrival_time": "10:00:51",
        "departure_time": "10:00:51",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4608",
        "stop_sequence": 42,
        "arrival_time": "10:01:50",
        "departure_time": "10:01:50",
        "timepoint": 1,
    },
    {
        "trip_id": "10536292",
        "stop_id": "4603",
        "stop_sequence": 43,
        "arrival_time": "10:03:00",
        "departure_time": "10:03:00",
        "timepoint": 1,
    },
]


TEST_BASIC = parse_obj_as(
    ScenarioDefinition,
    {
        "agency_id": "test_agency",
        "date": "2022-09-02",
        "stop_times": STOP_TIMES_BASIC,
        "stops": STOPS_BASIC,
        "vehicle_positions": from_breadcrumbs(
            trip_id="10536292",
            vehicle_id="vehicle-a",
            breadcrumbs=[
                ("2022-01-01 14:13:50.000", 42.34400002, 101.12500003),
                ("2022-01-01 14:15:50.000", 42.34400002, 101.12500003),
                ("2022-01-01 14:15:50.000", 42.34400002, 101.12500003),
                ("2022-01-01 14:15:50.000", 42.34400002, 101.12500003),
                ("2022-01-01 14:15:50.000", 42.34400002, 101.12500003),
            ],
        ),
    },
)


TEST_WHOLE_ROUTE = parse_obj_as(
    ScenarioDefinition,
    {
        "agency_id": "test_agency",
        "date": "2022-09-02",
        "stop_times": STOP_TIMES_BASIC,
        "stops": STOPS_BASIC,
        "vehicle_positions": from_file(
            trip_id="10536292",
            vehicle_id="vehicle-a",
            file_path="util/data/vehicle_positions__whole_trip.csv",
        ),
    },
)
