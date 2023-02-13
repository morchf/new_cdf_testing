import json
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parent_dir)

from FeaturePersistence import lambda_handler  # noqa: E402

print("*** deleting any existing test features ***")
delete_all_test = {
    "httpMethod": "DELETE",
    "queryStringParameters": {"AgencyGUID": "a10c7e57-0000-0000-0000-000000000000"},
}
response = lambda_handler(delete_all_test, "__main__ delete_all_test")


print("\n*** starting single feature test ***")
create_single_test = {
    "httpMethod": "POST",
    "body": json.dumps(
        # FeaturePersistenceItem
        {
            "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
            "FeatureName": "gtfs-realtime",
            "Feature": {
                "subscribed_till": None,
                "alerts_url": "https://test.alert.url",
                "trip_updates_url": "http://test.trip.url",
                "vehicle_positions_url": "http://test.vehicle.url",
                "max_polling_rate": 30,
                "vehicle_id_field": "id",
            },
        }
    ),
}
response = lambda_handler(create_single_test, "__main__ create_single_test")
assert response["statusCode"] == 200, response

invalid_post_single_test = {
    "httpMethod": "POST",
    "body": json.dumps(
        # FeaturePersistenceItem
        {
            "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
            "FeatureName": "gtfs-realtime",
            "Feature": {
                "subscribed_till": None,
                "alerts_url": "https://test.alert.url",
                "trip_updates_url": "http://test.trip.url",
                "vehicle_positions_url": "http://test.vehicle.url",
                "max_polling_rate": 30,
                "vehicle_id_field": "id",
            },
        }
    ),
}
response = lambda_handler(invalid_post_single_test, "__main__ invalid_post_single_test")
assert response["statusCode"] == 409, response

update_single_test = {
    "httpMethod": "PUT",
    "body": json.dumps(
        # FeaturePersistenceItem
        {
            "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
            "FeatureName": "gtfs-realtime",
            "Feature": {
                "subscribed_till": None,
                "alerts_url": "https://updated.alert.url",
                "trip_updates_url": "http://updated.trip.url",
                "vehicle_positions_url": "http://updated.vehicle.url",
                "max_polling_rate": 30,
                "vehicle_id_field": "id",
            },
        }
    ),
}
response = lambda_handler(update_single_test, "__main__ update_single_test")
assert response["statusCode"] == 200, response

patch_test = {
    "httpMethod": "PATCH",
    "body": json.dumps(
        {
            "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
            "FeatureName": "gtfs-realtime",
            "Feature": {
                "subscribed_till": "2022-09-20",
            },
        }
    ),
}
response = lambda_handler(patch_test, "__main__ update_test")
assert response["statusCode"] == 200, response

get_single_test1 = {
    "httpMethod": "GET",
    "queryStringParameters": {"AgencyGUID": "a10c7e57-0000-0000-0000-000000000000"},
}
response = lambda_handler(get_single_test1, "__main__ get_single_test1")
assert response["statusCode"] == 200, response

get_single_test2 = {
    "httpMethod": "GET",
    "queryStringParameters": {
        "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
        "FeatureName": "gtfs-realtime",
    },
}
response = lambda_handler(get_single_test2, "__main__ get_single_test2")
assert response["statusCode"] == 200, response

delete_single_test = {
    "httpMethod": "DELETE",
    "queryStringParameters": {
        "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
        "FeatureName": "gtfs-realtime",
    },
}
response = lambda_handler(delete_single_test, "__main__ delete_single_test")
assert response["statusCode"] == 200

print("\n*** starting multiple feature test ***")
create_multiple_test = {
    "httpMethod": "POST",
    "body": json.dumps(
        # AgencyFeatures
        {
            "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
            "Features": {
                "gtfs-realtime": {
                    "subscribed_till": None,
                    "alerts_url": "https://test.alert.url",
                    "trip_updates_url": "http://test.trip.url",
                    "vehicle_positions_url": "http://test.vehicle.url",
                    "max_polling_rate": 30,
                    "vehicle_id_field": "id",
                },
                "tsp-analytics": {
                    "early_schedule_deviation_limit": -5,
                    "late_schedule_deviation_limit": 2,
                    "peak_am_range": {
                        "start_time": "8:00:00",
                        "end_time": "9:30:00",
                    },
                    "peak_pm_range": {
                        "start_time": "4:30:00",
                        "end_time": "6:30:00",
                    },
                    "data_available_from": "2022-07-12",
                    "maximum_signal_delay": 300,
                    "geofencing_distance_meters": 50,
                },
            },
        }
    ),
}
response = lambda_handler(create_multiple_test, "__main__ create_multiple_test")
assert response["statusCode"] == 200

update_multiple_test = {
    "httpMethod": "PUT",
    "body": json.dumps(
        # FeatureAgencies
        {
            "FeatureName": "gtfs-realtime",
            "Features": {
                "a10c7e57-0000-0000-0000-000000000000": {
                    "subscribed_till": None,
                    "alerts_url": "https://test.alert.url",
                    "trip_updates_url": "http://test.trip.url",
                    "vehicle_positions_url": "http://test.vehicle.url",
                    "max_polling_rate": 30,
                    "vehicle_id_field": "id",
                },
                "a10c7e57-0000-0000-0000-000000000001": {
                    "subscribed_till": None,
                    "alerts_url": "https://test2.alert.url",
                    "trip_updates_url": "http://test2.trip.url",
                    "vehicle_positions_url": "http://test2.vehicle.url",
                    "max_polling_rate": 30,
                    "vehicle_id_field": "id",
                },
            },
        },
    ),
}
response = lambda_handler(update_multiple_test, "__main__ update_multiple_test")
assert response["statusCode"] == 200

# get all features from test agency
get_multiple_test1 = {
    "httpMethod": "GET",
    "queryStringParameters": {"AgencyGUID": "a10c7e57-0000-0000-0000-000000000000"},
}
response = lambda_handler(get_multiple_test1, "__main__ get_multiple_test1")
assert response["statusCode"] == 200

get_multiple_test2 = {
    "httpMethod": "GET",
    "queryStringParameters": {
        "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
        "FeatureName": "gtfs-realtime",
    },
}
response = lambda_handler(get_multiple_test2, "__main__ get_multiple_test2")
assert response["statusCode"] == 200

get_multiple_test3 = {
    "httpMethod": "GET",
    "queryStringParameters": {
        "AgencyGUID": "a10c7e57-0000-0000-0000-000000000000",
        "FeatureName": "tsp-analytics",
    },
}
response = lambda_handler(get_multiple_test3, "__main__ get_multiple_test3")
assert response["statusCode"] == 200

get_multiple_test4 = {
    "httpMethod": "GET",
    "queryStringParameters": {
        "FeatureName": "gtfs-realtime",
    },
}
response = lambda_handler(get_multiple_test4, "__main__ get_multiple_test4")
assert response["statusCode"] == 200

get_multiple_test5 = {
    "httpMethod": "GET",
    "queryStringParameters": {
        "FeatureName": "tsp-analytics",
    },
}
response = lambda_handler(get_multiple_test5, "__main__ get_multiple_test5")
assert response["statusCode"] == 200

# delete all features for an agency
delete_all_test = {
    "httpMethod": "DELETE",
    "queryStringParameters": {"AgencyGUID": "a10c7e57-0000-0000-0000-000000000000"},
}
response = lambda_handler(delete_all_test, "__main__ delete_all_test")
assert response["statusCode"] == 200

delete_all_test = {
    "httpMethod": "DELETE",
    "queryStringParameters": {"AgencyGUID": "a10c7e57-0000-0000-0000-000000000001"},
}
response = lambda_handler(delete_all_test, "__main__ delete_all_test")
assert response["statusCode"] == 200
