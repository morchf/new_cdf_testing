import logging
import os
from typing import Any, ClassVar, Dict, Optional

import boto3
from redis import Redis

from gtt.data_model.rt_radio_message import RTRadioMessage
from gtt.data_model.rt_radio_message.gps_data import GPSData

from .cache import MetadataCache


class IoTCoreService:
    """Utility class for building and publishing RTRadio Messages to AWS IoT Core"""

    # Standard topic format for MQTT messages going out to a VPS. The topic
    # currently must say 'EVP' even for TSP messages, but this may be changed in
    # future VPS updates. {device_type} is either 2100 (for EVP) or 2101 (for TSP)
    _topic_fmt: ClassVar[
        str
    ] = "GTT/{agency_cms_id}/SVR/EVP/{device_type}/{gtt_serial}/RTRADIO/{lat_lon}"

    redis: Redis
    iot_client: Any

    _topics: Dict[str, str]
    _messages: Dict[str, RTRadioMessage]
    _metadata_cache: MetadataCache

    def __init__(
        self,
        redis: Optional[Redis] = None,
        iot_client: Any = None,
    ) -> None:
        """params:
        - redis (optional): Redis connection instance to use for caching data related
            to RTRadio Messages. If not provided, will try to create one using the
            env variables 'REDIS_URL' and 'REDIS_PORT'
        - iot_client (optional): boto3 "iot-data" client to use. If not provided, one
            will be instantiated
        """
        self.redis = redis or Redis(
            host=os.getenv("REDIS_URL"),
            port=int(os.getenv("REDIS_PORT")),
            decode_responses=True,
        )
        self.redis.ping()  # Ensure connected
        self.iot_client = iot_client or boto3.client("iot-data")

        self._topics = {}
        self._messages = {}
        self._metadata_cache = MetadataCache(self.redis)

    def update(
        self,
        device_id: str,
        gps_data: GPSData = None,
        left_turn: bool = None,
        right_turn: bool = None,
        operational: bool = None,
        has_gps_fix: bool = None,
        gps_cstat: int = 0,
    ):
        """Modifies and publishes the RTRadioMessage associated with device 'device_id'.

        params:
        - device_id: The CDF id of the integration device
        - gps_data (optional): GPSData object with which to update both the payload
            and the topic
        - left_turn (optional): Whether the left blinker is on
        - right_turn (optional): Whether the right blinker is on
        - operational (optional): Whether the vehicle is operational, i.e. light bar
            is on
        - has_gps_fix (optional): Whether there is a gps fix
        - gps_cstat (optional): Input GPS CStat value, to be transformed depending
            on `has_gps_fix`. Defaults to 0, since none of the integrations currently
            provide it.

        example:
        ```python
        iot_service = IoTCoreService()
        iot_service.update(
            "my-agency-vehicle-1",
            gps_data=gps_data_from_device,
            left_turn=True,
            right_turn=False,
            operational=True,
            has_gps_fix=False,
        )
        ```
        """
        message = self._get_message(device_id) or self._build_message_base(device_id)
        updated = False

        if gps_data is not None:
            updated = True
            topic = self._build_and_cache_topic(device_id, gps_data)

            lat_min_degrees, lon_min_degrees = gps_data.minute_degrees()

            message.veh_gps_lat_ddmmmmmm = lat_min_degrees
            message.veh_gps_lon_dddmmmmmm = lon_min_degrees
            message.veh_gps_vel_mpsd5 = int(gps_data.speed * 5)
            message.veh_gps_hdg_deg2 = int(gps_data.heading / 2 + 0.5)
        else:
            topic = self.get_topic(device_id)

        if not topic:
            raise ValueError("No topic found; missing gps_data")

        if left_turn is not None:
            updated = True
            if left_turn:
                message.veh_mode_op_turn |= 1 << 0
            else:
                message.veh_mode_op_turn &= ~(1 << 0)
        if right_turn is not None:
            updated = True
            if right_turn:
                message.veh_mode_op_turn |= 1 << 1
            else:
                message.veh_mode_op_turn &= ~(1 << 1)
        if operational is not None:
            updated = True
            if operational:
                message.veh_mode_op_turn |= 1 << 2
            else:
                message.veh_mode_op_turn &= ~(1 << 2)

        # Todo: check with devices team to find out if this GPS fix/CStat stuff should
        # be deprecated. None of the current integrations provide a gps_cstat value,
        # so it's being set to 0, making this mostly redundant.
        if has_gps_fix is not None:
            updated = True
            message.veh_gps_cstat = gps_cstat
            if has_gps_fix:
                message.veh_gps_cstat &= 0x3FFF
            else:
                message.veh_gps_cstat |= 0xC000

        new_message = RTRadioMessage.validate(message)
        self.publish(topic, new_message)

        if updated:
            self._cache_message(device_id, new_message)

    def publish(self, topic: str, message: RTRadioMessage) -> None:
        logging.debug(f"Sending RTRadioMessage on {topic}")
        self.iot_client.publish(topic=topic, qos=0, payload=message.pack("little"))

    def get_topic(self, device_id: str) -> Optional[str]:
        return self._topics.get(device_id) or self.redis.get(
            f"rt_radio_message:{device_id}:topic"
        )

    def get_gps_data(self, device_id: str) -> Optional[GPSData]:
        message = self._get_message(device_id)
        if message is None:
            return None
        return message.gps_data()

    def get_left_turn(self, device_id: str) -> Optional[bool]:
        message = self._get_message(device_id)
        if message is None:
            return None
        return bool(message.veh_mode_op_turn & 1)

    def get_right_turn(self, device_id: str) -> Optional[bool]:
        message = self._get_message(device_id)
        if message is None:
            return None
        return bool(message.veh_mode_op_turn >> 1 & 1)

    def get_op_status(self, device_id: str) -> Optional[bool]:
        message = self._get_message(device_id)
        if message is None:
            return None
        return bool(message.veh_mode_op_turn >> 2 & 1)

    def _get_message(self, device_id: str) -> Optional[RTRadioMessage]:
        message = self._messages.get(device_id)
        if message:
            return message
        message_hex = self.redis.get(f"rt_radio_message:{device_id}:payload")
        if not message_hex:
            return None
        message = RTRadioMessage.unpack(message_hex, "little")
        self._messages[device_id] = message
        return message

    def _cache_message(self, device_id: str, message: RTRadioMessage):
        self.redis.set(
            f"rt_radio_message:{device_id}:payload", message.pack("little").hex()
        )
        self._messages[device_id] = message

    def _build_message_base(self, device_id: str) -> RTRadioMessage:
        metadata = self._metadata_cache.get(device_id)
        return RTRadioMessage(
            veh_sn=metadata.veh_sn,
            veh_city_id=metadata.veh_city_id,
            veh_class=metadata.veh_class,
            veh_veh_id=metadata.veh_veh_id,
            veh_mode_op_turn=metadata.veh_mode << 5,
        )

    def _build_and_cache_topic(self, device_id: str, gps_data: GPSData) -> str:
        if not gps_data:
            raise ValueError("Need gps_data to build topic")
        metadata = self._metadata_cache.get(device_id)
        topic = self._topic_fmt.format(
            agency_cms_id=metadata.agency_cms_id,
            device_type="2100" if metadata.veh_mode == 0 else "2101",
            gtt_serial=metadata.gtt_serial,
            lat_lon=gps_data.lat_lon(),
        )
        self.redis.set(f"rt_radio_message:{device_id}:topic", topic)
        self._topics[device_id] = topic
        return topic
