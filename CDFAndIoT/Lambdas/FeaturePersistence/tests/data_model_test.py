"""ToDo: tests to check
    - UUID assertion
    - GenericFeaturePersistenceItem
"""

from uuid import UUID

import requests

from gtt.data_model.feature_persistence import (
    AgencyFeatures,
    FeatureAgencies,
    FeatureNameEnum,
    GTFSRealtimeFeature,
    GTFSRealtimeItem,
    TimeRange,
    TSPAnalyticsFeature,
    TSPAnalyticsItem,
)

feature_persistence_api = (
    "https://k02hcsidw5.execute-api.us-east-1.amazonaws.com/develop"
)

agency_guid = UUID("a10c7e57-0000-0000-0000-000000000000")
agency_guid2 = str(agency_guid)[:-1] + "1"

valid_gtfs_realtime_feature = gtfs_realtime_feature = GTFSRealtimeFeature(
    vehicle_positions_url="https://test.vehicle.url",
    trip_updates_url="http://test.trip.url",
    alerts_url="http://test.alert.url",
    vehicle_id_field="id",
    max_polling_rate=30,
    subscribed_till=None,
)
valid_gtfs_realtime_item = gtfs_realtime_item = GTFSRealtimeItem(
    agency_id=agency_guid,
    feature_name=FeatureNameEnum.gtfs_realtime,
    feature=gtfs_realtime_feature,
)

# delete any existing test items
response = requests.delete(feature_persistence_api, params={"AgencyGUID": agency_guid})
response = requests.delete(feature_persistence_api, params={"AgencyGUID": agency_guid2})

# create item
response = requests.post(
    feature_persistence_api, data=gtfs_realtime_item.json(by_alias=True)
)
assert response.status_code == 200

# get item
response = requests.get(
    feature_persistence_api,
    params=gtfs_realtime_item.dict(
        by_alias=True, include={"agency_id", "feature_name"}
    ),
)
assert GTFSRealtimeItem.parse_raw(response.content) == gtfs_realtime_item

# get all agency features
response = requests.get(
    feature_persistence_api,
    params=gtfs_realtime_item.dict(by_alias=True, include={"agency_id"}),
)
assert (
    AgencyFeatures.parse_raw(response.content).features.get(
        FeatureNameEnum.gtfs_realtime
    )
    == gtfs_realtime_item.feature
)

# update item
gtfs_realtime_item.feature = GTFSRealtimeFeature(
    vehicle_positions_url="https://updated.vehicle.url",
    trip_updates_url="http://updated.trip.url",
    alerts_url="http://updated.alert.url",
    vehicle_id_field="id",
    max_polling_rate=30,
    subscribed_till=None,
)
# ensure only put overwrites
response = requests.post(
    feature_persistence_api, data=gtfs_realtime_item.json(by_alias=True)
)
assert response.status_code == 409
response = requests.put(
    feature_persistence_api, data=gtfs_realtime_item.json(by_alias=True)
)
assert response.status_code == 200

# patch item
gtfs_realtime_item.feature.subscribed_till = "2022-09-20"
# recreate feature to validate
gtfs_realtime_item.feature = GTFSRealtimeFeature(**gtfs_realtime_item.feature.dict())
response = requests.patch(
    feature_persistence_api,
    data=gtfs_realtime_item.json(
        by_alias=True,
        include={
            "agency_id": True,
            "feature_name": True,
            "feature": {"subscribed_till"},
        },
    ),
)
assert response.status_code == 200

# delete item
response = requests.delete(
    feature_persistence_api,
    params={
        "AgencyGUID": agency_guid,
        "FeatureName": FeatureNameEnum.gtfs_realtime,
    },
)
assert response.status_code == 200

# create multi
gtfs_realtime_item = valid_gtfs_realtime_item
valid_tsp_analytics_feature = tsp_analytics_feature = TSPAnalyticsFeature(
    early_schedule_deviation_limit=-5,
    late_schedule_deviation_limit=2,
    peak_am_range=TimeRange(
        start_time="8:00:00",
        end_time="9:30:00",
    ),
    peak_pm_range=TimeRange(
        start_time="4:30:00",
        end_time="6:30:00",
    ),
    data_available_from="2022-07-12",
    maximum_signal_delay=300,
    geofencing_distance_meters=50,
)
valid_tsp_analytics_item = tsp_analytics_item = TSPAnalyticsItem(
    agency_id=agency_guid,
    feature_name=FeatureNameEnum.tsp_analytics,
    feature=valid_tsp_analytics_feature,
)

# create items using AgencyFeatures object
agency_features = AgencyFeatures(
    agency_id=agency_guid,
    features={
        FeatureNameEnum.tsp_analytics: tsp_analytics_feature,
        FeatureNameEnum.gtfs_realtime: gtfs_realtime_feature,
    },
)
response = requests.post(
    feature_persistence_api,
    data=agency_features.json(by_alias=True),
)
assert response.status_code == 200

# get multiple as AgencyFeatures object
response = requests.get(feature_persistence_api, params={"AgencyGUID": agency_guid})
assert response.status_code == 200
assert AgencyFeatures.parse_raw(response.content) == agency_features

# get each as single FeaturePersistenceItem
response = requests.get(
    feature_persistence_api,
    params={"AgencyGUID": agency_guid, "FeatureName": FeatureNameEnum.tsp_analytics},
)
assert response.status_code == 200
assert TSPAnalyticsItem.parse_raw(response.content).feature == tsp_analytics_feature

response = requests.get(
    feature_persistence_api,
    params={
        "AgencyGUID": agency_guid,
        "FeatureName": FeatureNameEnum.gtfs_realtime,
    },
)
assert response.status_code == 200
assert GTFSRealtimeItem.parse_raw(response.content).feature == gtfs_realtime_feature

# delete each individually
response = requests.delete(
    feature_persistence_api,
    params={
        "AgencyGUID": agency_guid,
        "FeatureName": FeatureNameEnum.gtfs_realtime,
    },
)
assert response.status_code == 200
response = requests.delete(
    feature_persistence_api,
    params={
        "AgencyGUID": agency_guid,
        "FeatureName": FeatureNameEnum.gtfs_realtime,
    },
)
assert response.status_code == 200

# create multiple as FeatureAgencies object
feature_agencies = FeatureAgencies(
    feature_name=FeatureNameEnum.gtfs_realtime,
    features={
        agency_guid: gtfs_realtime_feature,
        agency_guid2: gtfs_realtime_feature,
    },
)
response = requests.put(
    feature_persistence_api,
    data=feature_agencies.json(by_alias=True),
)
assert response.status_code == 200

# get multiple as FeatureAgencies object
response = requests.get(
    feature_persistence_api, params={"FeatureName": FeatureNameEnum.gtfs_realtime}
)
assert response.status_code == 200
features = FeatureAgencies.parse_raw(response.content).features.items()
assert {str(agency_guid): gtfs_realtime_feature} in features

response = requests.get(
    feature_persistence_api, params={"FeatureName": FeatureNameEnum.tsp_analytics}
)
assert response.status_code == 200
features = FeatureAgencies.parse_raw(response.content).features.items()
assert {str(agency_guid): tsp_analytics_feature} in features

# delete all items from agency
response = requests.delete(feature_persistence_api, params={"AgencyGUID": agency_guid})
assert response.status_code == 200
response = requests.delete(feature_persistence_api, params={"AgencyGUID": agency_guid2})
assert response.status_code == 200
