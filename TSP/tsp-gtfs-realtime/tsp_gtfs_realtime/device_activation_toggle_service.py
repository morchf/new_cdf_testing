import json
import logging
import os
import random
import sys
from argparse import ArgumentParser
from datetime import timedelta
from enum import Enum
from typing import Any, ClassVar, Dict, List

import boto3
from gtt.service.asset_library import AssetLibraryAPI, Vehicle
from gtt.service.feature_persistence import FeaturePersistenceAPI
from redis import Redis

from gtt.data_model.asset_library import Template


class DeviceType(Enum):
    _2101: str = "2101"


class DeviceToggleService:
    # Singleton accessed via `asset_library_api()`
    __asset_lib_api: ClassVar[AssetLibraryAPI] = None
    # Singleton accessed via `iot_core()`
    __iot_core_client: ClassVar[Any] = None

    agency_id: str
    redis: Redis

    def __init__(self, agency_id: str, redis: Redis) -> None:
        self.agency_id = agency_id
        self.redis = redis
        self.update_vehicle_device_ids()

    def handle_tsp_toggle(self, msg: Dict[str, bytes]):
        """Redis PubSub handler for TSP Enabled messages. Enables or disables a
        2101 based on the state of the received message"""
        # Get vehicle_id from pubsub message
        vehicle_id = msg["data"].decode()
        # Get SetTSPEnabled JSON object from redis
        tsp_toggle_obj = json.loads(
            self.redis.get(f"tsp_in_cloud:tsp_enabled:{self.agency_id}:{vehicle_id}")
        )
        is_enabled = 0 if tsp_toggle_obj["enabled"] is True else 1
        # Try to get serial number from associated communicator
        try:
            serial_number = self.get_comm_serial(vehicle_id=vehicle_id)
        except Exception as e:
            logging.error(f"Error toggling device: {e}")
            return
        self.build_and_send_iot_message(serial_number=serial_number, state=is_enabled)

    def build_and_send_iot_message(self, serial_number, state):
        """
        This is the method that builds up the SCP message to sent to IoTCore.
        state - This should be 0 if DISABLE and 1 if ENABLE. This enabled and disables the PROBE setting on the debice.
        serial_number - This should be the serial number of the device to send a message to.

        Notes:
        idx has to be a unique value per request sent to the device.
        Get the current value from redis and increment it by 1 to be unique.
        The randint() is a fallback if redis fails.
        """
        # Construct Data Packet : Referred from: https://github.com/gtt/smart-city-platform/blob/develop/CEI/CEIBackend/CEI_EVP_Activation.py#L72
        try:
            redis_idx_key = "tsp_in_cloud:device_activation_2101:idx_value"
            idx = int(self.redis.get(redis_idx_key) or random.randint(1, 100000) + 1)
            if idx > sys.maxsize:
                self.redis.set(redis_idx_key, 1)
            else:
                self.redis.set(redis_idx_key, idx + 1)
        except Exception as redis_idx_exception:
            logging.exception(f"Unable to fetch idx from Redis: {redis_idx_exception=}")
        command_id = 49  # This is 31h in decimal.
        message_id = idx.to_bytes(4, byteorder="big")
        msgData = state  # This is the state of the vehicle to be sent.
        checksum = (
            command_id
            + message_id[0]
            + message_id[1]
            + message_id[2]
            + message_id[3]
            + msgData
        ).to_bytes(2, byteorder="big")
        messageArray = [
            command_id,
            message_id[0],
            message_id[1],
            message_id[2],
            message_id[3],
            0,
            0,
            0,
            0,
            msgData,
            checksum[0],
            checksum[1],
        ]
        logging.debug(f"{bytearray(messageArray)=}")
        try:
            # Construct IoT Topic
            topic = f"GTT/GTT/SVR/TSP/2101/{serial_number}/STATE"
            response = self.iot_core().publish(
                topic=topic,
                qos=0,
                payload=bytearray(messageArray),
            )
            logging.info(
                f"Message published to topic: {topic} to change PROBE state to: {state}"
            )
            logging.debug(f"Response from IoTCore: {response}")
            if response:
                return response
            else:
                raise Exception("Unable to send message to IoTCore")
        except Exception as IoTCorePublishException:
            logging.exception(IoTCorePublishException)
            return

    def get_comm_serial(self, vehicle_id: str):
        """Looks for communicator serial in redis first, then tries to get it from
        asset library. Raises Exception if not found in either"""
        redis_key = (
            f"tsp_in_cloud:communicator_serials:{self.agency_id}:vid:{vehicle_id}"
        )
        serial = self.redis.get(redis_key)
        if serial is None:
            serial = self.get_comm_serial_from_asset_lib(vehicle_id=vehicle_id)
            self.redis.set(redis_key, serial)
            # Expire in COMM_SERIAL_TTL minutes, or default one hour
            self.redis.expire(
                redis_key, timedelta(minutes=int(os.environ.get("COMM_SERIAL_TTL", 60)))
            )
        else:
            serial = serial.decode()
        return serial

    def get_comm_serial_from_asset_lib(self, vehicle_id: str):
        """Tries to get the serial number of the communicator associated with the
        vehicle that has a VID of 'vehicle_id' from the Asset Library. If no such
        communicator exists, raises an Exception"""
        device_id_key = (
            f"tsp_in_cloud:vehicle_device_ids:{self.agency_id}:vid:{vehicle_id}"
        )
        if self.redis.exists(device_id_key) == 0:
            self.update_vehicle_device_ids()
        device_id = self.redis.get(device_id_key)
        vehicle: Vehicle = self.asset_library_api().get_device(
            device_id=device_id.decode()
        )
        for device in vehicle.installed_devices:
            if device.template_id == Template.Communicator:
                return device.gtt_serial
        raise Exception(f"No associated Communicator for vehicle: {vehicle_id}")

    def update_vehicle_device_ids(self) -> Dict[str, str]:
        agency = self.asset_library_api().get_agency_by_id(self.agency_id.upper())
        vehicles: List[Vehicle] = [
            device
            for device in agency.devices
            if device.template_id == Template.Vehicle
        ]
        for vehicle in vehicles:
            key = f"tsp_in_cloud:vehicle_device_ids:{self.agency_id}:vid:{vehicle.VID}"
            self.redis.set(key, vehicle.device_id)
            self.redis.expire(key, timedelta(days=1))

    def asset_library_api(self) -> AssetLibraryAPI:
        """Singleton accessor"""
        if self.__class__.__asset_lib_api is None:
            self.__class__.__asset_lib_api = AssetLibraryAPI()
        return self.__class__.__asset_lib_api

    def iot_core(self) -> Any:
        """Singleton accessor"""
        if self.__class__.__iot_core_client is None:
            self.__class__.__iot_core_client = boto3.client("iot-data")
        return self.__class__.__iot_core_client


def main():

    # CLI Argument Parser
    parser = ArgumentParser(description="Spawn new vehicle subscriber containers")
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=str, help="port for redis endpoint")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    # Configure Logging
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)  # noqa
    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    # Configure Redis
    redis_url = args.redis_url or os.getenv("REDIS_URL") or "localhost"
    redis_port = int(args.redis_port or os.getenv("REDIS_PORT") or 6379)
    redis = Redis(host=redis_url, port=redis_port)
    logging.debug(redis.ping())

    # Find all 2101 agencies
    device_togglers: List[DeviceToggleService] = []
    try:
        point_to_point_agencies = FeaturePersistenceAPI().get_feature_agencies(
            feature_name=os.getenv("FEATURE_NAME")
            or "tsp-asm-2101"  # this is tsp-asm-2101 if its a 2101 device.
        )
    except Exception as e:
        logging.info(f"Error getting point-to-point agencies: {e}")
        point_to_point_agencies = {}

    for agency_id, feature in point_to_point_agencies.items():
        device_type = feature.get("device_type")
        if device_type is None or DeviceType(device_type) != DeviceType._2101:
            logging.info(
                f"Unsupported device type for agency: {agency_id}: '{device_type}'"
            )
            continue
        device_togglers.append(DeviceToggleService(agency_id=agency_id, redis=redis))
        logging.debug(f"Added {agency_id} to DeviceToggle list")

    # Subscribe each DeviceToggleService to its respective Redis channel pattern
    pubsub = redis.pubsub()
    subscriptions = {}
    for device_toggler in device_togglers:
        subscribe_channel = f"tsp_in_cloud:new_tsp_enabled:{device_toggler.agency_id}:*"
        subscriptions[subscribe_channel] = device_toggler.handle_tsp_toggle
        logging.info(f"Subscribing to {subscribe_channel}")
    pubsub.psubscribe(**subscriptions)
    pubsub.run_in_thread(sleep_time=60, daemon=False)

    logging.info(
        "Device activation toggle service running. Waiting for TSP enabled messages"
    )


if __name__ == "__main__":
    main()
