from typing import Dict, Optional

from gtt.service.asset_library import AssetLibraryAPI, Device
from pydantic import BaseModel
from redis import Redis


class Metadata(BaseModel):
    veh_sn: int
    veh_city_id: int
    veh_class: int
    veh_veh_id: int

    veh_mode: int
    gtt_serial: str
    agency_unique_id: str
    agency_cms_id: str


class MetadataCache:
    _redis: Redis
    _metadata: Dict[str, Metadata]
    _asset_lib_api: AssetLibraryAPI

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._metadata = {}
        self._asset_lib_api = AssetLibraryAPI()

    def clear(self, device_id: str) -> bool:
        """Removes metadata from local memory and the redis cache; returns True
        if it was in either and False if it was in neither"""
        was_in_memory = self._metadata.pop(device_id, False)
        deleted_keys = self._redis.delete(f"rt_radio_message:device_fields:{device_id}")
        return was_in_memory or deleted_keys > 0

    def clear_soft(self, device_id: str) -> bool:
        """Removes metadata from local memory but NOT the redis cache; returns
        True if it was in local memory and False if it was not"""
        return self._metadata.pop(device_id, False)

    def clear_all(self) -> None:
        """Removes all metadata from local memory and the redis cache"""
        self._redis.delete(self._redis.keys("rt_radio_message:device_fields:*"))
        self._metadata = {}

    def clear_all_soft(self) -> None:
        """Removes all metadata from local memory but NOT the redis cache"""
        self._metadata = {}

    def get(self, device_id: str) -> Metadata:
        """Tries to get metadata first from local memory, then from the redis
        cache, and then from the asset library"""
        # Try local memory
        device_data = self.get_from_local(device_id)
        if device_data:
            return device_data

        # Try Redis
        device_data = self.get_from_cache(device_id)
        if device_data:
            self._set_local(device_id, device_data)
            return device_data

        # Try Asset Library
        device_data = self.get_from_asset_library(device_id)
        self._set_local(device_id, device_data)
        self._set_redis(device_id, device_data)
        return device_data

    def get_from_local(self, device_id: str) -> Optional[Metadata]:
        return self._metadata.get(device_id)

    def get_from_cache(self, device_id: str) -> Optional[Metadata]:
        device_json = self._redis.get(f"rt_radio_message:device_fields:{device_id}")
        if device_json:
            return Metadata.parse_raw(device_json)

    def get_from_asset_library(self, device_id: str) -> Optional[Metadata]:
        device: Device = self._asset_lib_api.get_device(device_id)
        agency = self._asset_lib_api.get_agency(device.region_name, device.agency_name)

        end_of_mac_address = int(device.address_mac.replace(":", "")[-6:], 16)
        veh_sn = 0x800000 | end_of_mac_address
        vehicle_mode = 0 if device.vehicle.priority.lower() == "high" else 1

        return Metadata(
            veh_sn=veh_sn,
            veh_class=device.vehicle.class_,
            veh_veh_id=device.vehicle.VID,
            veh_mode=vehicle_mode,
            gtt_serial=device.gtt_serial,
            agency_unique_id=agency.unique_id.lower(),
            agency_cms_id=agency.cms_id.lower(),
            veh_city_id=agency.agency_code,
        )

    def _set_local(self, device_id: str, device_data: Metadata):
        self._metadata[device_id] = device_data

    def _set_redis(self, device_id: str, device_data: Metadata):
        self._redis.set(
            f"rt_radio_message:device_fields:{device_id}", device_data.json()
        )
