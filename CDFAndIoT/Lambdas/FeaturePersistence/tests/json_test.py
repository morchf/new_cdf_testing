"""ToDo: tests to check
    - UUID assertion
    - GenericFeaturePersistenceItem
    - FeatureAgencies
"""

import json
from uuid import UUID

import requests

feature_persistence_api = (
    "https://k02hcsidw5.execute-api.us-east-1.amazonaws.com/develop"
)

agency_guid = UUID("a10c7e57-0000-0000-0000-000000000000")

valid_gtfs_realtime_feature = gtfs_realtime_feature = {
    "vehicle_positions_url": "https://test.vehicle.url",
    "trip_updates_url": "http://test.trip.url",
    "alerts_url": "http://test.alert.url",
    "vehicle_id_field": "id",
    "max_polling_rate": 30.0,
    "subscribed_till": None,
}
valid_gtfs_realtime_item = gtfs_realtime_item = {
    "AgencyGUID": str(agency_guid),
    "FeatureName": "gtfs-realtime",
    "Feature": gtfs_realtime_feature,
}

# delete any existing test items
response = requests.delete(feature_persistence_api, params={"AgencyGUID": agency_guid})

# create item
response = requests.post(feature_persistence_api, json=gtfs_realtime_item)
assert response.status_code == 200

# get item
response = requests.get(
    feature_persistence_api,
    params={"AgencyGUID": str(agency_guid), "FeatureName": "gtfs-realtime"},
)
assert response.status_code == 200
assert json.loads(response.content) == gtfs_realtime_item

# get all agency features
response = requests.get(
    feature_persistence_api,
    params={"AgencyGUID": str(agency_guid)},
)
assert response.status_code == 200
feature = json.loads(response.content).get("Features", {}).get("gtfs-realtime")
assert feature == gtfs_realtime_item["Feature"]

# update item
gtfs_realtime_item["Feature"] = {
    "vehicle_positions_url": "https://updated.vehicle.url",
    "trip_updates_url": "http://updated.trip.url",
    "alerts_url": "http://updated.alert.url",
    "vehicle_id_field": "id",
    "max_polling_rate": 30.0,
    "subscribed_till": None,
}
# ensure only put overwrites
response = requests.post(feature_persistence_api, json=gtfs_realtime_item)
assert response.status_code == 409
response = requests.put(feature_persistence_api, json=gtfs_realtime_item)
assert response.status_code == 200

# patch item
gtfs_realtime_item["Feature"]["subscribed_till"] = "2022-09-20"
response = requests.patch(
    feature_persistence_api,
    json={
        "AgencyGUID": gtfs_realtime_item["AgencyGUID"],
        "FeatureName": gtfs_realtime_item["FeatureName"],
        "Feature": {
            "subscribed_till": gtfs_realtime_item["Feature"]["subscribed_till"]
        },
    },
)
assert response.status_code == 200

# delete item
response = requests.delete(
    feature_persistence_api,
    params={
        "AgencyGUID": gtfs_realtime_item["AgencyGUID"],
        "FeatureName": gtfs_realtime_item["FeatureName"],
    },
)
assert response.status_code == 200

# create multi
gtfs_realtime_item = valid_gtfs_realtime_item
valid_tsp_analytics_feature = tsp_analytics_feature = {
    "early_schedule_deviation_limit": -5,
    "late_schedule_deviation_limit": 2,
    "peak_am_range": {
        "start_time": "08:00:00",
        "end_time": "09:30:00",
    },
    "peak_pm_range": {
        "start_time": "04:30:00",
        "end_time": "06:30:00",
    },
    "data_available_from": "2022-07-12",
    "maximum_signal_delay": 300,
    "geofencing_distance_meters": 50,
}
valid_tsp_analytics_item = tsp_analytics_item = {
    "AgencyGUID": str(agency_guid),
    "FeatureName": "tsp-analytics",
    "Feature": valid_tsp_analytics_feature,
}

# create items using AgencyFeatures object
agency_features = {
    "AgencyGUID": str(agency_guid),
    "Features": {
        "tsp-analytics": tsp_analytics_feature,
        "gtfs-realtime": gtfs_realtime_feature,
    },
}
response = requests.post(feature_persistence_api, json=agency_features)
assert response.status_code == 200

# get multiple as AgencyFeatures object
response = requests.get(feature_persistence_api, params={"AgencyGUID": agency_guid})
assert response.status_code == 200
assert json.loads(response.content) == agency_features

# get each as single FeaturePersistenceItem
response = requests.get(
    feature_persistence_api,
    params={"AgencyGUID": str(agency_guid), "FeatureName": "tsp-analytics"},
)
assert response.status_code == 200
assert json.loads(response.content)["Feature"] == tsp_analytics_feature

response = requests.get(
    feature_persistence_api,
    params={"AgencyGUID": str(agency_guid), "FeatureName": "gtfs-realtime"},
)
assert response.status_code == 200
assert json.loads(response.content)["Feature"] == gtfs_realtime_feature

# get multiple as FeatureAgencies object
response = requests.get(
    feature_persistence_api, params={"FeatureName": "gtfs-realtime"}
)
assert response.status_code == 200
features = json.loads(response.content)["Features"].items()
assert {str(agency_guid): gtfs_realtime_feature} in features

response = requests.get(
    feature_persistence_api, params={"FeatureName": "tsp-analytics"}
)
assert response.status_code == 200
features = json.loads(response.content)["Features"].items()
assert {str(agency_guid): tsp_analytics_feature} in features

# delete all items from agency
response = requests.delete(feature_persistence_api, params={"AgencyGUID": agency_guid})
assert response.status_code == 200
