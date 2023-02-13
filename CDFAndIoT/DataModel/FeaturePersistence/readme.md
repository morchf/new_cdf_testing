# FeaturePersistence Data Model
This library is to aid development by using a shared data model library for the backend and the frontend. This will enable much simpler data validation and (de)serialization and force this library to be the source of truth so that any service interacting with the data will be be responsible for handling changes.

## Installation
From root repo folder, else update the path to be this folder

``` bash
pip install -e CDFAndIoT/DataModel/FeaturePersistence
```

For local develop, include the `-e` flag to allow an editable install

## Usage
Using feature class directly

``` python
from gtt.data_model.feature_persistence import GTFSRealtimeItem, GTFSRealtimeFeature, FeatureNameEnum

feature = GTFSRealtimeFeature(
    vehicle_positions_url="https://vehicle_positions.url",
    trip_updates_url="https://trip_updates.url",
    alerts_url="https://alerts.url",
    subscribed_till=None,
    max_polling_rate=15.0,
    vehicle_id_field="id",
)

item = GTFSRealtimeItem(
    agency_id="agencyid-uuid-431a-b790-0fb6e4832244",
    feature_name=FeatureNameEnum.gtfs_realtime,
    feature=feature,
)

repr(item)
```

> GTFSRealtimeItem(agency_id='agencyid-uuid-431a-b790-0fb6e4832244', feature_name=<FeatureNameEnum.gtfs_realtime: 'gtfs-realtime'>, feature=GTFSRealtimeFeature(vehicle_positions_url='https://vehicle_positions.url', trip_updates_url='https://trip_updates.url', alerts_url='https://alerts.url', vehicle_id_field='id', max_polling_rate=15.0, subscribed_till=None))

Instantiating subclass using parent

``` python
from pydantic import parse_obj_as
from gtt.data_model.feature_persistence import FeaturePersistenceItem

# parsed json returned from FeaturePersistence API
feature = dict(
    agency_id="agencyid-uuid-431a-b790-0fb6e4832244",
    feature_name="gtfs-realtime",
    feature=dict(
        vehicle_positions_url="https://vehicle_positions.url",
        trip_updates_url="https://trip_updates.url",
        alerts_url="https://alerts.url",
        subscribed_till=None,
        max_polling_rate=15.0,
        vehicle_id_field="id",
    ),
)

# raw json can be parsed with parse_json(feature)
item = parse_obj_as(FeaturePersistenceItem, feature)

repr(item)
```

> GTFSRealtimeItem(agency_id='agencyid-uuid-431a-b790-0fb6e4832244', feature_name=<FeatureNameEnum.gtfs_realtime: 'gtfs-realtime'>, feature=GTFSRealtimeFeature(vehicle_positions_url='https://vehicle_positions.url', trip_updates_url='https://trip_updates.url', alerts_url='https://alerts.url', vehicle_id_field='id', max_polling_rate=15.0, subscribed_till=None))
