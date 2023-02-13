"""ToDo: use actual UUIDs and expand to better test coverage"""

from gtt.service.asset_library import AssetLibraryAPI

asset_library_api = AssetLibraryAPI()

ic_device_id = "tsp-gtfs-realtime-643"
invalid_ic_device_id = "tsp-gtfs-realtime-543"
ic_serial_search_attributes = {"serial": 643}

vehicle_device_id = "union-city-vehicle-643"
invalid_vehicle_device_id = "union-city-vehicle-543"
vehicle_name_search_attributes = {"name": "vehicle-643"}

# case insensitive
region_name = "UnionCity"
agency_name = "uNiOncITy"
region_path = f"/{region_name}"
agency_path = f"/{region_name}/{agency_name}"
display_name_search_attributes = {"displayName": "UnionCity"}

# instantiate IntegrationCom using either device_id or search
integration_com_0 = asset_library_api.get_device(ic_device_id)
integration_com_1 = asset_library_api.get_device(
    asset_library_api.find_device_id("integrationcom", **ic_serial_search_attributes)
)

# print and show that both are equivalent
print(integration_com_0)
print(f"{(integration_com_0 == integration_com_1)=}")

# instantiate Communicator using either device_id or search
communicator_0 = asset_library_api.get_device(ic_device_id)
communicator_1 = asset_library_api.get_device(
    asset_library_api.find_device_id("communicator", **ic_serial_search_attributes)
)

# print and show that both are equivalent
print(communicator_0)
print(f"{(communicator_0 == communicator_1)=}")

# instantiate Vehicle using either device_id or search
vehicle_0 = asset_library_api.get_device(device_id=vehicle_device_id)
vehicle_1 = asset_library_api.get_device(
    asset_library_api.find_device_id("vehiclev2", **vehicle_name_search_attributes)
)

# ! It seems like it is not possible to search using VID because "eq" requires the field
# ! to be a string type, but VID is a number. Using gte, lte, etc. timed out after 30s

# print and show that both are equivalent
print(vehicle_0)
print(f"{(vehicle_0 == vehicle_1)=}")

# instantiate Agency using either group_path or search
agency_0 = asset_library_api.get_agency(region_name, agency_name)
agency_1 = asset_library_api.get_group(
    asset_library_api.find_group_path("agency", **display_name_search_attributes)
)

# print and show that both are equivalent
print(agency_0)
print(f"{(agency_0 == agency_1)=}")

# instantiate Region using either group_path or search
region_0 = asset_library_api.get_region(region_name)
region_1 = asset_library_api.get_group(
    asset_library_api.find_group_path("region", **display_name_search_attributes)
)

# print and show that both are equivalent
print(region_0)
print(f"{(region_0 == region_1)=}")

# bidirectional between vehicle/ic
print(f"{(integration_com_0.vehicle == vehicle_0)=}")
print(f"{(vehicle_0.integration_com == integration_com_0)=}")

# bidirectional between vehicle/com
print(f"{(communicator_0.vehicle == vehicle_0)=}")
print(f"{(vehicle_0.communicator == communicator_0)=}")

# bidirectional between agency/device or region
print(
    f"{(integration_com_0.agency == vehicle_0.agency == agency_0 == region_0.agencies[0])=}"
)
print(
    f"{(integration_com_0.region == vehicle_0.region == agency_0.region == region_0)=}"
)

# device in list from group collection
print(f"{(communicator_0 in agency_0.communicators)=}")
print(f"{(integration_com_0 in agency_0.integration_coms)=}")
print(f"{(vehicle_0 in agency_0.vehicles)=}")
print(
    f"{all(d in agency_0.devices for d in [communicator_0, communicator_1, integration_com_0, integration_com_1, vehicle_0, vehicle_1])=}"
)
print(
    f"{all(d in region_0.agencies[0].devices for d in [communicator_0, communicator_1, integration_com_0, integration_com_1, vehicle_0, vehicle_1])=}"
)
