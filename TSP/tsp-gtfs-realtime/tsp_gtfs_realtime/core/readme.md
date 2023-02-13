# TSP GTFS Realtime Core
This library contains code that is shared by the running services. These are relatively simple abstractions but should provide a simple way to have shared functionality among services.

Actual elasticache creation and connection is not currently implemented, but it should follow that a shared configuration can be created/managed here.

from `tsp_gtfs_realtime.core`, the following classes can be imported:
- [AWSConfig](#awsconfig)
- [AWSRedisBase](#awsredisbase)
- [AWSRedisSubscriber](#awsredissubscriber)
- [CDFConfig](#cdfconfig)
- [CDFClient](#cdfclient)

## Usage
Creating a Config object (AWSConfig and CDFConfig) is currently necessary to specify the connection parameters. This can be replaced in the future by environment variables or requiring a call to the CDF API.

## AWS
This module is to facilitate connection to AWS Services and provide basic abstraction around core functionality

### `AWSRedisBase`
A class that connects to a configured redis instance and provides a `redis` attribute, which instantiates a [redis-py](https://redis-py.readthedocs.io/en/stable/index.html) object. Using the `Config` class (which can be imported from `core` as `AWSConfig`) it can be configured to point to a local/standalone Redis server or to an AWS-managed elasticache instance.

### `AWSRedisSubscriber`
An inherited class that connects the same and also provides a `pubsub` attribute which is a redis messaging feature to subscribe to messages from some publisher. Once initialized, an inherited class can subscribe to a single topic or a pattern using subscribe or psubscribe, respectively.

### `AWSConfig`
Although the code has never been tested in this way, it should be relatively trivial to create a `Config` class that points to an elasticache instance. Ideally, the elasticache instance will also be created or configured within this codebase so this access data can be stored to a file and retrieved by subsequent instances so they will not to query aws to find the endpoint information.

There are a number of methods and options to configure and create a redis connection/pipeline, so it might make sense to allow providing a redis instance directly

|            option | type |  default  | description |
| ----------------: | :--: | :-------: | :---------- |
| local_development | bool | True      | This might be unnecessary depending on what initial authorization is needed for elasticache |
| redis_url         | str  | localhost | The hostname for the redis endpoint. [More complex url schemes](https://redis-py.readthedocs.io/en/stable/index.html#redis.Redis.from_url) are available, but this is not currently implemented. |
| redis_port        | int  | 6379      | |
| use_ssl           | bool | False     | Not used by default, but elasticache likely requires it |
| username          | bool | False     | Not used by default, but elasticache likely requires it |
| password          | bool | False     | Not used by default, but elasticache likely requires it |

## CDF
This module is provides an abstraction around the CDF entities, and provides functionality around core IoT concepts. Currently it exists to create an RT Radio Message using the necessary CDF Entity attributes, but it will likely be expanded to handle any required CDF API querying.

Depending on development scope, it might make sense to mostly decouple this from the low-level AWS services and only have it represent a data model of CDF entities and other objects that semantically exist within IoT Core, either as a connection to or an abstraction of the CDF Asset Library.

### `CDFClient`
A class that currently resembles CreateRTRADIOMsg.py, and provides the ability to create an RT Radio topic and message by querying the CDF API for the required attributes and publishing it to IoT core.

Currently, the connections to gtfs realtime data are not there, and the CDF data is faked. Depending on the CDF entity update policy (or how lazily to load CDF data), it needs to be determined what connections and coupling are required. The lambdas depend on the DynamoDB cache (or ElastiCache) for lazy loading, resorting to the CDF API if not in the cache. For this long-running service, data can simply be stored in a class variable upon instantiation to remove the coupling to the cache that is required for the lambdas. If the Agency Manager knows about CDF changes, all attributes can be known at runtime, with changes handled by the Agency Manager.

This will remain an open question for now, but refactoring this class to be more general-purpose will be kept flexible.

### `CDFConfig`
Although the code has never been tested in this way, it should be relatively trivial to create a `Config` class that points to the CDF API endpoint.

|            option | type |  default  | description |
| ----------------: | :--: | :-------: | :---------- |
| local_development | bool | True      | This might be unnecessary depending on what initial authorization is needed for elasticache |
| aws_region        | str  | us-east-2 | The AWS region where the CDF API exists |
| cdf_url           | str  | localhost | The full URL for the CDF API endpoint |

## GTFS Realtime API Poller
This library provides subscriber and parsing functionality for a GTFS Realtime feed.

from `tsp_gtfs_realtime.gtfs_realtime`, the following classes can be imported:
- [GTFSRealtimeConfig](#gtfsrealtimeconfig)
- [GTFSRealtimeAPIPoller](#gtfsrealtimeapipoller)

### `GTFSRealtimeAPIPoller`
A class that connects to an agency that provides one or more GTFS Realtime feeds. The max polling rate is enforced by blocking the thread when a feed is polled until the max polling period has passed. This is enforced on a feed-level by default, but it can also be enforced on an agency-level which would lower the overall polling rate if multiple feeds are being used. More information about multiple feeds and each feed type can be found [below](#feed-information).

To poll for vehicle positions (similarly for trip updates and alerts), the `poll_vehicle_positions()` function will query the gtfs feed for new data, parse the returned protobuf, and make the data available using the `vehicle_positions` attribute. When this attribute is accessed, a list of all the new data is provided as a tuple for each vehicle, `(vehicle_id, attributes)`, where attributes is a flattened dictionary that can be fed directly to a redis hash.

### `GTFSRealtime`
The agency information that is needed for the gtfs realtime api poller can be loaded from the feature persistence API or a dict/json file with the same fields. This class is a pydantic class that enables validation to ensure the input parameters are valid. The typical way of instantiating this class is the class factory function, `from_inputs()`, but it can also be instantiated like any pydantic BaseModel class using a keyword args, dict, json, etc.

When instantiating using `from_inputs`, if `should_query_feature_api` is set to True, the function queries the Feature Persistence API and returns the object created by deserializing the json response from the API (`feature_api_url` and `agency_id` should also be set). If `should_query_feature_api` is False, the object is created by deserializing a json file. If `config_file` is set, it uses this path; otherwise it loads the default config file. A warning is logged if `config_file` and `should_query_feature_api` are both set.

from_inputs:
|                   option |   type   | default | description |
| -----------------------: | :------: | :-----: | :---------- |
| feature_api_url          | HttpUrl  |         | base Feature Persistence API endpoint. Required if `should_query_feature_api` |
| agency_id                | str      |         | agency_id matching the Feature Persistence AgencyGUID. Required if `should_query_feature_api` |
| should_query_feature_api | bool     | False   | whether to query feature persistence api |
| config_file              | FilePath | tsp_gtfs_realtime/config/gtfs-realtime-api-poller.json | path to json config file to load |

When instantiating using the [typical pydantic style](https://pydantic-docs.helpmanual.io/usage/models/) or with the loaded json, the following values are used. At least one API endpoint URL is required.

|                option |      type     | default | description |
| --------------------: | :-----------: | :-----: | :---------- |
| vehicle_positions_url | HttpUrl       |         | endpoint_url for VehiclePositions feed |
| trip_updates_url      | HttpUrl       |         | endpoint_url for TripUpdates feed |
| alerts_url            | HttpUrl       |         | endpoint_url for Alerts feed |
| vehicle_id_field      | "id", "label" | "id"    | which VehicleDescriptor field to identify a vehicle |
| max_polling_rate      | PositiveFloat | 15      | minimum time between subsequent feed polls |
| use_agency_max_rate   | bool          | False   | whether to apply the max rate to all feeds. Default is per-feed rate |
| subscribed_till       | date          |         | reserved for future use |

## Feed Information
The [GTFS Realtime Protobuf Specification](https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto) provides three entity types: TripUpdate, VehiclePosition, and Alert. When a Feed is retrieved, it contains some metadata and optional fields for each of these entities. Even though they all can be present at the same URL and in the same message, in practice most agencies provide a URL for each of these entity types independently. Because of this, an abstracted `GTFSRealtimeFeed` object is instantiated for each of these entity types to handle the actual api request and parsing, while enforcing feed-level polling frequency restrictions.

There are a number of extensions to GTFS Realtime that are experimental, and agencies can also add custom extension data. A few agencies either additionally or exclusively provide a "Trapeze" feed URL, which seems to be related to the Mobility Company of the same name. This URL was one of the few that provided the entity types together, and it might make sense to extend use to this feed type; [Duluth Transit](https://www.duluthtransit.com/home/doing-business/developer-resources/#:~:text=ZIP%20FILE-,Real%20Time%20Feed,-.JSONE) is one agency which provides this feed. Some agencies also provide a custom realtime API that allows querying per-vehicle or per-trip, for example, and it might make sense to utilize these in the future if it is easy to extend a custom solution for these agencies; [ACTransit's realtime API is one example](https://api.actransit.org/transit/Help#ActRealtime).

For each of the three entity types, the value is flattened and returned, even though optional fields might not actually be populated by an agency. It might make sense to only provide data that is populated, but then the subscriber would need to check for the existence of a particular field instead of just looking at its value. Additionally, it might make sense to actually have multiple hash sets instead of purely flattening this message. This would make sense if wanting to just access/query by trip_id. Between each of the three entity types there is overlapped data, so there might be less latency for a particular piece of data.

### Vehicle Position
The [VehiclePosition message](https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto#:~:text=message%20VehiclePosition) contains metadata and vehicle information, position, and current trip objects. When getting a list of these messages after a poll, these nested objects are flattened to a single dictionary with clarified naming when necessary (trip.direction_id is changed to trip_direction_id, for example). It should be noted that these are mostly optional. speed and bearing can be estimated from subsequent position messages and refined using knowledge of road shape, but knowing momentary values will likely show much more

|                  name |  protobuf object  | type  | description |
| --------------------: | :---------------: | :---: | :---------- |
| timestamp             |                   | int   | POSIX time in seconds |
| current_stop_sequence |                   | int   | numerical index of stop, from stop_times.txt |
| stop_id               |                   | str   | unique stop identifier from stops.txt |
| current_status        |                   | int   | integer of enum value, can be changed to string if needed |
| congestion_level      |                   | int   | integer of enum value, can be changed to string if needed |
| occupancy_status      |                   | int   | integer of enum value, can be changed to string if needed |
| vehicle_id            | VehicleDescriptor | str   | unique vehicle identifier, typically used as FeedEntity.id |
| vehicle_label         | VehicleDescriptor | str   | user-level vehicle identifier |
| license_plate         | VehicleDescriptor | str   | license plate number |
| latitude              | Position          | float | degrees North, in the WGS-84 coordinate system |
| longitude             | Position          | float | degrees East, in the WGS-84 coordinate system |
| bearing               | Position          | float | bearing, in degrees, clockwise from North |
| odometer              | Position          | float | odometer value, in meters |
| speed                 | Position          | float | momentary speed of the vehicle, in meters per second |
| trip_id               | TripDescriptor    | str   | trip identifier, not guaranteed unique from trips.txt |
| route_id              | TripDescriptor    | str   | route identifier from routes.txt |
| trip_direction_id     | TripDescriptor    | int   | prepended trip_, direction identifier from trips.txt |
| trip_start_time       | TripDescriptor    | str   | prepended trip_, scheduled start time of this trip instance |
| trip_start_date       | TripDescriptor    | str   | prepended trip_, scheduled start date of this trip instance |
| schedule_relationship | TripDescriptor    | int   | integer of enum value, can be changed to string if needed |

### Trip Update
The [TripUpdate message](https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto#:~:text=message%20TripUpdate) contains metadata and trip, vehicle, and repeated stop timing information. When getting a list of these messages after a poll, these nested objects are flattened to a single dictionary with clarified naming when necessary (trip.direction_id is changed to trip_direction_id, for example). The `stop_time_updates` are a list, and may need to be handled separately. Vehicle-specific information (including predictions) is presented from the perspective of stops along a trip.

|                  name |  protobuf object  | type | description |
| --------------------: | :---------------: | :--: | :---------- |
| timestamp             |                   | int  | POSIX time in seconds |
| delay                 |                   | int  | experimental estimate for schedule deviation, in seconds |
| trip_id               | TripDescriptor    | str  | trip identifier, not guaranteed unique from trips.txt |
| route_id              | TripDescriptor    | str  | route identifier from routes.txt |
| trip_direction_id     | TripDescriptor    | int  | prepended trip_, direction identifier from trips.txt |
| trip_start_time       | TripDescriptor    | str  | prepended trip_, scheduled start time of this trip instance |
| trip_start_date       | TripDescriptor    | str  | prepended trip_, scheduled start date of this trip instance |
| schedule_relationship | TripDescriptor    | int  | integer of enum value, can be changed to string if needed |
| vehicle_id            | VehicleDescriptor | str  | prepended vehicle_, unique vehicle identifier |
| vehicle_label         | VehicleDescriptor | str  | prepended vehicle_, user-level vehicle identifier |
| license_plate         | VehicleDescriptor | str  | license plate number |
| stop_time_updates     | StopTimeUpdate    | list | repeated, prediction for each stop event, see below for details |

|                  name | protobuf object | type | description |
| --------------------: | :-------------: | :--: | :---------- |
| stop_sequence         |                 | int  | numerical index of stop, from stop_times.txt |
| stop_id               |                 | str  | unique stop identifier from stops.txt |
| arrival_delay         | StopTimeEvent   | int  | prepended arrival_, delay in seconds, negative is ahead of schedule |
| arrival_time          | StopTimeEvent   | int  | prepended arrival_, absolute time, scheduled plus delay |
| arrival_uncertainty   | StopTimeEvent   | int  | prepended arrival_, error most likely in seconds, 0 is certain |
| departure_delay       | StopTimeEvent   | int  | prepended departure_,  delay in seconds, negative is ahead of schedule |
| departure_time        | StopTimeEvent   | int  | prepended departure_, absolute time, scheduled plus delay |
| departure_uncertainty | StopTimeEvent   | int  | prepended departure_, error most likely in seconds, 0 is certain |

### Alert
The [Alert message](https://developers.google.com/transit/gtfs-realtime/gtfs-realtime-proto#:~:text=message%20Alert) contains metadata, timing, and alert information, along with lists of active periods and affected entities. When getting a list of these messages after a poll, these nested objects are flattened to a single dictionary with clarified naming when necessary (trip.direction_id is changed to trip_direction_id, for example). The `active_periods` and `informed_entities` are lists, and may need to be handled separately. This message will likely not be used for vehicle position estimation.

|                       name | protobuf object | type | description |
| -------------------------: | :-------------: | :--: | :---------- |
| header_text                |                 | int  | short summary in plain text |
| description_text           |                 | int  | full description in plain text |
| additional_information_url |                 | str  | url that contains additional information about the alert |
| cause                      |                 | int  | integer of enum value, can be changed to string if needed |
| effect                     |                 | int  | integer of enum value, can be changed to string if needed |
| active_periods             | TimeRange       | list | repeated, when alert applies, see below for details |
| informed_entities          | EntitySelector  | list | repeated, entities affected, see below for details |

|  name | protobuf object | type | description |
| ----: | :-------------: | :--: | :---------- |
| start |                 | int  | start of time range |
| end   |                 | int  | end of time range |

|                       name | protobuf object | type | description |
| -------------------------: | :-------------: | :--: | :---------- |
| agency_id                  |                 | str  | unique agency identifier from agency.txt |
| route_id                   |                 | str  | unique route identifier from routes.txt |
| route_type                 |                 | int  | the type of transportation used on route from routes.txt |
| stop_id                    |                 | str  | unique stop identifier from stops.txt |
| trip_id                    | TripDescriptor  | str  | trip identifier, not guaranteed unique from trips.txt |
| trip_route_id              | TripDescriptor  | str  | prepended trip_, route identifier from routes.txt |
| trip_direction_id          | TripDescriptor  | int  | prepended trip_, direction identifier from trips.txt |
| trip_start_time            | TripDescriptor  | str  | prepended trip_, scheduled start time of this trip instance |
| trip_start_date            | TripDescriptor  | str  | prepended trip_, scheduled start date of this trip instance |
| trip_schedule_relationship | TripDescriptor  | int  | prepended trip_, integer of enum value, can be changed to string if needed |

## Potential Improvements
Originally, this was separated into its own module in case it made sense to build a
compiled library. This can still be done if needed, likely having a compiled service that does all of the elasticache updating/messaging.

### http handling
sometimes, a response has "Content-Length" in the http header, other times it is "Transfer-Encoding": "chunked". When "Content-Length is there, it usually has "Warning": "110 Response is stale". An http conditional response might be possible to spare bandwidth and overhead.
