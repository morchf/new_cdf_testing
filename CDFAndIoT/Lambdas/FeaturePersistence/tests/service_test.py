"""ToDo: tests to check
    - UUID assertion
"""
from uuid import UUID

from pydantic import parse_obj_as

from gtt.data_model.feature_persistence import (
    AgencyFeatureDict,
    AgencyFeatures,
    FeatureAgencies,
    FeatureNameEnum,
    FeatureNameFeatureDict,
    GTFSRealtimeFeature,
    TimeRange,
    TSPAnalyticsFeature,
)
from gtt.service.feature_persistence import FeaturePersistenceAPI

feature_persistence_api = FeaturePersistenceAPI(
    url="https://k02hcsidw5.execute-api.us-east-1.amazonaws.com/develop"
)

agency_id = UUID("a10c7e57-0000-0000-0000-000000000000")
agency_id2 = UUID(str(agency_id)[:-1] + "1")

gtfs_realtime_feature = GTFSRealtimeFeature(
    vehicle_positions_url="https://test.vehicle.url",
    trip_updates_url="http://test.trip.url",
    alerts_url="http://test.alert.url",
    vehicle_id_field="id",
    max_polling_rate=30,
    subscribed_till=None,
)
valid_gtfs_realtime_feature = gtfs_realtime_feature.copy(deep=True)

# delete any existing test items
feature_persistence_api.delete(agency_id=agency_id, quiet=True)
feature_persistence_api.delete(agency_id=agency_id2, quiet=True)

# create item
feature_persistence_api.create_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
    feature=gtfs_realtime_feature,
)

# get item
response_feature = feature_persistence_api.get_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
)
assert response_feature == gtfs_realtime_feature

# get all agency features
response_features = feature_persistence_api.get_agency_features(agency_id=agency_id)
assert response_features.get(FeatureNameEnum.gtfs_realtime) == gtfs_realtime_feature


# update item
updated_gtfs_realtime_feature = GTFSRealtimeFeature(
    vehicle_positions_url="https://updated.vehicle.url",
    trip_updates_url="http://updated.trip.url",
    alerts_url="http://updated.alert.url",
    vehicle_id_field="id",
    max_polling_rate=30,
    subscribed_till=None,
)
# ensure only put overwrites
try:
    feature_persistence_api.create_feature(
        agency_id=agency_id,
        feature_name=FeatureNameEnum.gtfs_realtime,
        feature=updated_gtfs_realtime_feature,
    )
    raise Exception
except Exception as e:
    assert type(e) == ValueError
feature_persistence_api.create_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
    feature=updated_gtfs_realtime_feature,
    force=True,
)

# patch item
gtfs_realtime_feature.subscribed_till = "2022-09-20"
# recreate feature to validate
gtfs_realtime_feature = GTFSRealtimeFeature(**gtfs_realtime_feature.dict())
feature_persistence_api.patch_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
    # feature=gtfs_realtime_feature.dict(by_alias=True, include={"subscribed_till"}),
    subscribed_till=gtfs_realtime_feature.subscribed_till,
)

# delete item
feature_persistence_api.delete_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
)

# create multi
gtfs_realtime_feature = valid_gtfs_realtime_feature
tsp_analytics_feature = TSPAnalyticsFeature(
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

# create items using AgencyFeatures object
features = parse_obj_as(
    FeatureNameFeatureDict,
    {
        FeatureNameEnum.tsp_analytics: tsp_analytics_feature.dict(by_alias=True),
        FeatureNameEnum.gtfs_realtime: gtfs_realtime_feature.dict(by_alias=True),
    },
)
agency_features = AgencyFeatures(agency_id=agency_id, features=features)

feature_persistence_api.create(agency_features)

# get multiple as AgencyFeatureDict
response_features = feature_persistence_api.get_agency_features(agency_id=agency_id)
assert response_features == features

# get each as single FeaturePersistenceFeature
response_feature = feature_persistence_api.get_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.tsp_analytics,
)
assert response_feature == tsp_analytics_feature

response_feature = feature_persistence_api.get_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
)
assert response_feature == gtfs_realtime_feature

# delete each individually
feature_persistence_api.delete_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.gtfs_realtime,
)
feature_persistence_api.delete_feature(
    agency_id=agency_id,
    feature_name=FeatureNameEnum.tsp_analytics,
)

# create multiple as FeatureAgencies object
gtfs_realtime_features = parse_obj_as(
    AgencyFeatureDict,
    {
        agency_id: gtfs_realtime_feature,
        agency_id2: gtfs_realtime_feature,
    },
)
feature_agencies = FeatureAgencies(
    feature_name=FeatureNameEnum.gtfs_realtime, features=gtfs_realtime_features
)
feature_persistence_api.create(feature_agencies, force=True)

tsp_analytics_features = parse_obj_as(
    AgencyFeatureDict,
    {
        agency_id: tsp_analytics_feature,
        agency_id2: tsp_analytics_feature,
    },
)
feature_agencies = FeatureAgencies(
    feature_name=FeatureNameEnum.tsp_analytics, features=tsp_analytics_features
)
feature_persistence_api.create(feature_agencies, force=True)

# get multiple as FeatureAgencyDict
response_features = feature_persistence_api.get_feature_agencies(
    feature_name=FeatureNameEnum.gtfs_realtime
)
assert gtfs_realtime_features[agency_id] in response_features.values()
assert gtfs_realtime_features[agency_id2] in response_features.values()

response_features = feature_persistence_api.get_feature_agencies(
    FeatureNameEnum.tsp_analytics
)
assert (str(agency_id), tsp_analytics_feature) in response_features.items()
assert (str(agency_id2), tsp_analytics_feature) in response_features.items()

# delete all items from agency
feature_persistence_api.delete(agency_id=agency_id)
feature_persistence_api.delete(agency_id=agency_id2)
