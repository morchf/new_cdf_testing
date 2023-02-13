import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, ForwardRef, List, Literal, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.types import NonNegativeInt, conint

from .util import coordinates_to_offset, merge, offset_to_coordinates

PhaseSelectorMessage = ForwardRef("PhaseSelectorMessage")


class PhaseSelectorDeviceType(Enum):
    Wildcard = 0xFF
    OpticomPhaseSelector = 0x00
    CanogaDetector = 0x01
    OpticomGPSPhaseSelector = 0x02
    OpticomGPSVehicleUnit = 0x03
    Opticom462PhaseSelector = 0x04
    Opticom464PhaseSelector = 0x05
    Opticom762PhaseSelector = 0x06
    Opticom7652PhaseSelector = 0x07
    Opticom764PhaseSelector = 0x08
    Opticom7654PhaseSelector = 0x09
    Opticom761GateOpener = 0x0A
    Opticom7651GateOpener = 0x0B
    Opticom210xVehicleUnit = 0x0C
    Opticom215xVehicleUnit = 0x0D
    Opticom310xRadioUnit = 0x0E
    Opticom315xRadioUnit = 0x0F
    Opticom7605PhaseSelector = 0x10
    Opticom7655PhaseSelector = 0x11
    Opticom22xxLowCostVehicleUnit = 0x12
    ReservedCentralizedVehicle = 0x16
    ReservedCentralizedIntersection = 0x17


class PhaseSelectorOutputType(Enum):
    NONE = 0
    REAR1 = 1
    REAR2 = 2
    REAR3 = 3
    REAR4 = 4
    AIP1 = 5
    AIP2 = 6
    AIP3 = 7
    AIP4 = 8
    AIP5 = 9
    AIP6 = 10
    AIP7 = 11
    AIP8 = 12
    AIP9 = 13
    AIP10 = 14
    AIP11 = 15
    AIP12 = 16
    AIP13 = 17
    AIP14 = 18
    AIP15 = 19
    AIP16 = 20
    SELECT_BY_CLASS = 21
    SELECT_BY_COND_PRIORITY = 22


class PhaseSelectorAddressType(Enum):
    SerialAddress = 0x0
    Address = 0x1
    Wildcard = 0x2
    Wildcard2 = 0x3


# Wildcard device ID constants
WILDCARD_DEVICE_TYPE = PhaseSelectorDeviceType.Wildcard.value
WILDCARD_ADDRESS_TYPE = PhaseSelectorAddressType.Wildcard.value
WILDCARD_ADDRESS = 0x00

EtaThreshold = conint(ge=0, le=255)
# DistanceThreshold = conint(ge=0, le=5000)
DistanceThreshold = conint(ge=0)


class OutputChannel(
    BaseModel, allow_population_by_field_name=True, use_enum_values=True
):
    channel: Optional[str]
    channel_name: Optional[str] = Field(alias="channelName")
    format_version: Optional[int] = Field(alias="formatVersion")
    logical_channel: Optional[NonNegativeInt] = Field(alias="logicalChannel")
    phases: Optional[List[NonNegativeInt]]
    high_priority_preempts: Optional[List[NonNegativeInt]] = Field(
        alias="highPriorityPreempts"
    )
    low_priority_preempts: Optional[List[NonNegativeInt]] = Field(
        alias="lowPriorityPreempts"
    )
    low_priority_queue_jump_preempt: Optional[int] = Field(
        alias="lowPriorityQueueJumpPreempt"
    )
    assigned_approaches: Optional[List[NonNegativeInt]] = Field(
        alias="assignedApproaches"
    )
    check_in_check_out_enabled: Optional[int] = Field(alias="checkInCheckOutEnabled")
    check_in_classes: Optional[List[NonNegativeInt]] = Field(alias="checkInClasses")
    check_in_entry_distance_threshold: Optional[conint(ge=0, le=5000)] = Field(
        alias="checkInEntryDistanceThreshold"
    )
    check_in_exit_distance_threshold: Optional[conint(ge=0, le=5000)] = Field(
        alias="checkInExitDistanceThreshold"
    )
    check_in_announcement_output: Optional[List[NonNegativeInt]] = Field(
        alias="checkInAnnouncementOutput"
    )
    check_out_entry_threshold: Optional[NonNegativeInt] = Field(
        alias="checkOutEntryThreshold"
    )
    forward_calls_in_forward_direction: Optional[NonNegativeInt] = Field(
        alias="forwardCallsInForwardDirection"
    )
    priority_outputs: Optional[List[NonNegativeInt]] = Field(alias="priorityOutputs")
    ignore_heading: Optional[NonNegativeInt] = Field(alias="ignoreHeading")
    preempt_plan_evp: Optional[List[NonNegativeInt]] = Field(alias="preemptPlanEvp")
    priority_plan_tsp: Optional[List[NonNegativeInt]] = Field(alias="priorityPlanTsp")


class TimeLocalizationDetails(BaseModel, allow_population_by_field_name=True):
    timezone: Optional[str] = Field(alias="timezone")
    utc_offset: Optional[str] = Field(alias="utcOffset")

    class Date(BaseModel):
        month: Optional[str]
        date: Optional[str]
        year: Optional[str]
        hours: Optional[str]
        minutes: Optional[str]
        rule: Optional[str]

    forward: Date
    reverse: Date


class ApproachMapEntry(
    BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
):
    approach_name: Optional[str] = Field(alias="approachName")
    number_of_coordinates: Optional[NonNegativeInt] = Field(alias="numberOfCoordinates")

    class Coordinate(
        BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
    ):
        latitude: Optional[float]
        x: Optional[int]
        longitude: Optional[float]
        y: Optional[int]
        width: Optional[NonNegativeInt] = 30

    coordinates: Optional[List[Coordinate]]


ApproachMap = List[ApproachMapEntry]


class ThresholdChannel(
    BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
):
    format_version: Optional[int] = Field(alias="formatVersion")
    priority: Optional[str]
    channel_name: Optional[str] = Field(alias="channelName")
    channel: Optional[str]
    call_bridging_enabled: Optional[NonNegativeInt] = Field(alias="callBridgingEnabled")
    call_bridging_time: Optional[NonNegativeInt] = Field(alias="callBridgingTime")
    proximity_threshold: Optional[NonNegativeInt] = Field(alias="proximityThreshold")

    class Channel(
        BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
    ):
        call_hold_time: Optional[NonNegativeInt] = Field(
            alias="lostSignalHold", default=0
        )

        # UI
        eta_thresholds: Optional[List[EtaThreshold]] = Field(alias="etaThresholds")
        distance_thresholds: Optional[List[DistanceThreshold]] = Field(
            alias="distanceThresholds"
        )
        max_call_time: Optional[NonNegativeInt] = Field(alias="maxCallTime")

        preempt_enabled: Optional[NonNegativeInt] = Field(alias="preemptEnabled")
        directional_priority: Optional[NonNegativeInt] = Field(
            alias="directionalPriority"
        )
        call_delay_time: Optional[NonNegativeInt] = Field(alias="callDelayTime")
        off_approach_hold_time: Optional[NonNegativeInt] = Field(
            alias="offApproachHoldTime"
        )
        primary_intensity_thresholds: Optional[List[NonNegativeInt]] = Field(
            alias="primaryIntensityThresholds"
        )
        auxiliary_intensity_thresholds: Optional[List[NonNegativeInt]] = Field(
            alias="auxiliaryIntensityThresholds"
        )

    @validator("format_version", pre=True)
    def handle_format_version_string(cls, format_version):
        if isinstance(format_version, str):
            return int(format_version, 16)

        return format_version

    class HighPriorityChannel(Channel):
        pass

    class LowPriorityChannel(Channel):
        reservice_enabled: Optional[NonNegativeInt] = Field(alias="reserviceEnabled")
        reservice_time: Optional[NonNegativeInt] = Field(alias="reserviceTime")

    high_priority: Optional[HighPriorityChannel] = Field(
        alias="highPriority", default_factory=Channel
    )
    low_priority: Optional[LowPriorityChannel] = Field(
        alias="lowPriority", default_factory=Channel
    )


class ConfigurationProfile(
    BaseModel,
    allow_population_by_field_name=True,
    arbitrary_types_allowed=True,
):
    format_version: Optional[int] = Field(alias="formatVersion")
    profile_type: Optional[int] = Field(alias="profileType")
    profile_index: Optional[int] = Field(alias="profileIndex")
    profile_name: Optional[str] = Field(alias="profileName")
    number_of_high_codes: Optional[int] = Field(alias="numberOfHighCodes")
    number_of_low_codes: Optional[int] = Field(alias="numberOfLowCodes")
    high_priority_relative_priorities_enabled: Optional[int] = Field(
        alias="highPriorityRelativePrioritiesEnabled"
    )
    high_priority_relative_priorities: Optional[List[NonNegativeInt]] = Field(
        alias="highPriorityRelativePriorities"
    )
    low_priority_relative_priorities_enabled: Optional[int] = Field(
        alias="lowPriorityRelativePrioritiesEnabled"
    )
    low_priority_relative_priorities: Optional[List[NonNegativeInt]] = Field(
        alias="lowPriorityRelativePriorities"
    )
    relative_priority_lockout_eta: Optional[int] = Field(
        alias="relativePriorityLockoutEta"
    )
    conditional_priority_enabled: Optional[int] = Field(
        alias="conditionalPriorityEnabled"
    )
    number_of_channels: Optional[NonNegativeInt] = Field(alias="numberOfChannels")
    low_codes: Optional[str] = Field(alias="lowCodes")
    high_codes: Optional[str] = Field(alias="highCodes")

    channels: Optional[List[ThresholdChannel]] = Field(default_factory=list)


# Derived fields


class ClassType(BaseModel, allow_population_by_field_name=True):
    level: str = Field(alias="class")
    name: str
    # active: Union[Literal["Y"], Literal["N"]]
    active: bool = True


LOW_PRIORITY_CLASS_TYPES = [
    ClassType(level="1", name="Regular Transit", active=True),
    ClassType(level="2", name="Express Transit", active=True),
    ClassType(level="3", name="Paratransit", active=True),
    ClassType(level="4", name="Light Rail", active=True),
    ClassType(level="5", name="Trolley", active=True),
    ClassType(level="6", name="Snow Plows", active=True),
    ClassType(level="7", name="Supervisor", active=True),
    ClassType(level="8", name="Pavement Marking", active=True),
    ClassType(level="9", name="Installer/Set-up", active=True),
    ClassType(level="10", name="Bus Rapid Transit", active=False),
    ClassType(level="11", name="Not used", active=False),
    ClassType(level="12", name="Not used", active=False),
    ClassType(level="13", name="Not used", active=False),
    ClassType(level="14", name="Not used", active=False),
    ClassType(level="15", name="Not used", active=False),
    ClassType(level="16", name="Not used", active=False),
]
HIGH_PRIORITY_CLASS_TYPES = [
    ClassType(level="1", name="Fire Rescue/EMT/Ambulance", active=True),
    ClassType(level="2", name="Engine/Pumper", active=True),
    ClassType(level="3", name="Ladder/Arial/Snorkel", active=True),
    ClassType(level="4", name="Brush", active=True),
    ClassType(level="5", name="Miscellaneous", active=True),
    ClassType(level="6", name="Fire Chief/Captain", active=True),
    ClassType(level="7", name="Supervisor", active=True),
    ClassType(level="8", name="Maintenance", active=True),
    ClassType(level="9", name="Installer/Set-up", active=True),
    ClassType(level="10", name="Police/Sheriff Cars", active=True),
    ClassType(level="11", name="Miscellaneous Police/Sheriff", active=True),
    ClassType(level="12", name="Police Chief/Supervisor", active=True),
    ClassType(level="13", name="Private Ambulance", active=True),
    ClassType(level="14", name="Not Used", active=True),
    ClassType(level="15", name="Base Station", active=True),
    ClassType(level="16", name="Not Used", active=True),
]


class Thresholds(
    BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
):
    class Channel(
        BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
    ):
        channel_name: Optional[str] = Field(alias="channelName")
        channel: Optional[str]
        call_hold_time: Optional[NonNegativeInt] = Field(alias="lostSignalHold")
        max_call_time: Optional[NonNegativeInt] = Field(alias="maxCallTime")

        class Class(
            ClassType, allow_population_by_field_name=True, arbitrary_types_allowed=True
        ):
            eta: Optional[conint(ge=0, le=255)]
            # distance: Optional[conint(ge=0, le=5000)]
            distance: Optional[conint(ge=0)]

        classes: Optional[List[Class]]

    low_priority: Optional[List[Channel]] = Field(alias="lowPriority")
    high_priority: Optional[List[Channel]] = Field(alias="highPriority")


class Outputs(
    BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
):
    class Output(
        BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
    ):
        type: Optional[str]

        class Channel(
            BaseModel, allow_population_by_field_name=True, arbitrary_types_allowed=True
        ):
            channel: Optional[str]
            straight: Optional[NonNegativeInt]
            left: Optional[NonNegativeInt]
            right: Optional[NonNegativeInt]

        channels: Optional[List[Channel]]

    low_priority: Optional[Output] = Field(alias="lowPriority")
    high_priority: Optional[Output] = Field(alias="highPriority")


class PhaseSelector(
    BaseModel,
    allow_population_by_field_name=True,
    use_enum_values=True,
    arbitrary_types_allowed=True,
):
    serial_number: str = Field(alias="serialNumber")
    location_type: Optional[Union[str, Literal["ntcip"]]] = Field(alias="locationType")
    # latitude: Optional[confloat(ge=-90, le=90)]
    latitude: Optional[float]
    # longitude: Optional[confloat(ge=-180, le=180)]
    longitude: Optional[float]
    make: Optional[Union[str, Literal["GTT"]]]
    model: Optional[Union[str, Literal["v764"]]]
    last_communicated: Optional[datetime] = Field(alias="lastCommunicated")
    # Literal["Central", "Mountain", "Eastern", "Pacific", "Arizona"]
    # Literal["CST", "PST"]
    timezone: Optional[str]
    operation_mode: Optional[str] = Field(alias="operationMode")
    status: Optional[Union[str, Literal["Normal"]]]
    firmware_version: Optional[str] = Field(alias="firmwareVersion")
    device_type: Optional[Union[int, PhaseSelectorDeviceType]] = Field(
        alias="deviceType"
    )
    # MAC address?
    address: Optional[str]
    address_type: Optional[Union[conint(ge=0, le=3), PhaseSelectorAddressType]] = Field(
        alias="addressType"
    )
    mac_address: Optional[str] = Field(alias="macAddress")
    unit_id: Optional[str] = Field(alias="unitId")
    device_name: Optional[str] = Field(alias="deviceName")
    time_localization_details: Optional[TimeLocalizationDetails] = Field(
        alias="timeLocalizationDetails"
    )
    last_configured: Optional[datetime] = Field(alias="lastConfigured")
    approach_offset: Optional[int] = Field(alias="approachOffset")

    # Approach map, thresholds, and outputs
    approach_map: Optional[ApproachMap] = Field(alias="approachMap")

    configuration_profile: Optional[ConfigurationProfile] = Field(
        alias="configurationProfile"
    )
    # High/low-priority thresholds with class definitions
    thresholds: Optional[Thresholds]

    channels: Optional[List[OutputChannel]]
    outputs: Optional[Outputs]

    is_configured: Optional[bool] = Field(alias="isConfigured", default=False)

    @root_validator()
    def convert_approach_map_coordinates(cls, values):
        approach_map = values.get("approach_map")
        intersection_latitude = values.get("latitude")
        intersection_longitude = values.get("longitude")

        if approach_map is None or len(approach_map) == 0:
            return values

        approach_map_entries = []

        for approach_map_entry in approach_map:
            coordinates = []
            for coordinate in approach_map_entry.coordinates:
                x, y, latitude, longitude = (0, 0, 0, 0)

                # Convert coordinates to offset
                if coordinate.x is not None and coordinate.y is not None:
                    latitude, longitude = offset_to_coordinates(
                        intersection_latitude,
                        intersection_longitude,
                        coordinate.x,
                        coordinate.y,
                    )
                    x, y = (coordinate.x, coordinate.y)
                if coordinate.latitude is not None and coordinate.longitude is not None:
                    x, y = coordinates_to_offset(
                        intersection_latitude,
                        intersection_longitude,
                        coordinate.latitude,
                        coordinate.longitude,
                    )
                    latitude, longitude = (coordinate.latitude, coordinate.longitude)

                coordinates.append(
                    ApproachMapEntry.Coordinate(
                        x=x, y=y, latitude=latitude, longitude=longitude
                    )
                )

            approach_map_entries.append(
                ApproachMapEntry(
                    **approach_map_entry.dict(exclude={"coordinates"}),
                    coordinates=coordinates,
                )
            )

        values.update(approach_map=approach_map_entries)

        return values

    @root_validator()
    def convert_thresholds(cls, values):
        """Package high/low-priority thresholds with class definitions

        Returns:
            Thresholds: High/low priority threshold channels
        """
        thresholds = values.get("thresholds")
        if thresholds is not None:
            return values

        configuration_profile = values.get("configuration_profile")

        if configuration_profile is None:
            return values

        low_priority_channels = []
        high_priority_channels = []

        for channel in configuration_profile.channels:
            low_priority_channels.append(
                Thresholds.Channel(
                    channel_name=channel.channel_name,
                    channel=channel.channel,
                    call_hold_time=channel.low_priority.call_hold_time,
                    max_call_time=channel.low_priority.max_call_time,
                    classes=[
                        Thresholds.Channel.Class(
                            level=ct.level,
                            name=ct.name,
                            active=ct.active,
                            eta=eta,
                            distance=distance,
                        )
                        for ct, eta, distance in zip(
                            LOW_PRIORITY_CLASS_TYPES,
                            channel.low_priority.eta_thresholds,
                            channel.low_priority.distance_thresholds,
                        )
                    ],
                )
            )
            high_priority_channels.append(
                Thresholds.Channel(
                    channel_name=channel.channel_name,
                    channel=channel.channel,
                    call_hold_time=channel.high_priority.call_hold_time,
                    max_call_time=channel.high_priority.max_call_time,
                    classes=[
                        Thresholds.Channel.Class(
                            level=ct.level,
                            name=ct.name,
                            active=ct.active,
                            eta=eta,
                            distance=distance,
                        )
                        for ct, eta, distance in zip(
                            HIGH_PRIORITY_CLASS_TYPES,
                            channel.high_priority.eta_thresholds,
                            channel.high_priority.distance_thresholds,
                        )
                    ],
                )
            )

        values.update(
            thresholds=Thresholds(
                low_priority=low_priority_channels,
                high_priority=high_priority_channels,
            )
        )

        return values

    @root_validator()
    def convert_outputs(cls, values):
        outputs = values.get("outputs")
        if outputs is not None:
            return values

        channels = values.get("channels")

        if channels is None:
            return values

        low_priority_output_channels = []
        high_priority_output_channels = []

        for channel in channels:
            straight, left, right = channel.priority_plan_tsp
            low_priority_output_channels.append(
                Outputs.Output.Channel(
                    channel=channel.channel, straight=straight, left=left, right=right
                )
            )

            straight, left, right = channel.preempt_plan_evp
            high_priority_output_channels.append(
                Outputs.Output.Channel(
                    channel=channel.channel, straight=straight, left=left, right=right
                )
            )

        outputs = Outputs(
            low_priority=Outputs.Output(
                type=None, channels=low_priority_output_channels
            ),
            high_priority=Outputs.Output(
                type=None, channels=high_priority_output_channels
            ),
        )
        values.update(outputs=outputs)

        return values

    @root_validator()
    def set_is_configured(cls, values):
        latitude = values.get("latitude")
        longitude = values.get("longitude")
        device_name = values.get("device_name")
        # TODO: Better determine configured status
        is_configured = not (
            latitude is None or latitude == 0 or longitude is None or longitude == 0
        ) or (device_name != "" or device_name is None)

        values.update(is_configured=is_configured)

        return values

    @classmethod
    def _device_id(
        cls,
        address: Optional[Union[str, int]] = None,
        address_type: Optional[int] = None,
        device_type: Optional[int] = None,
    ) -> str:
        """Convert device type, address type, and address to device ID

        4-bytes long

        .-----------------------||----------------------------------------||-----------------------------------.
        | * * * * * * * *       || * * . . . . . .      | . . * * * * * * || * * * * * * * * | * * * * * * * * |
        |-----------------------||----------------------------------------||-----------------------------------|
        | DeviceType (FF000000) || AddressType (C00000) | Address (3FFFFF)                                     |
        .-----------------------||----------------------------------------||-----------------------------------|

        Returns:
            str: Hex representation of device ID
        """
        if isinstance(address, str):
            address = int(address, 16)

        device_id = (
            ((WILDCARD_ADDRESS if address is None else address) & 0x3FFFFF)
            + (
                (
                    (WILDCARD_ADDRESS_TYPE if address_type is None else address_type)
                    << 22
                )
                & 0xC00000
            )
            + (
                ((WILDCARD_DEVICE_TYPE if device_type is None else device_type) << 24)
                & 0xFF000000
            )
        )

        return f"{device_id:2X}"

    @property
    def device_id(self) -> str:
        if self.address_type is None:
            address_type = (
                # Regular: 00b or 01b
                0x2
                if self.address is not None
                # Wildcard: 10b or 11b
                else 0x0
            )

        return PhaseSelector._device_id(self.address, address_type, self.device_type)

    @classmethod
    def wildcard_device_id(cls) -> int:
        return PhaseSelector._device_id()


class PhaseSelectorBuilder:
    def __init__(self):
        self._partials = []

    def add_partial(
        self, partial: Dict[str, Any], message: Optional[PhaseSelectorMessage] = None
    ):
        if message:
            logging.debug(f"Adding response from message type {message.__name__}")

        self._partials.append(partial)

    def build(self):
        phase_selector = {}
        try:
            for partial in self._partials:
                for k, v in partial.items():
                    merge(phase_selector, {k: v})

            phase_selector = PhaseSelector(**phase_selector)
            # For both high and low thresholds
            for (_, threshold_channels) in phase_selector.thresholds:
                for channel_index, threshold_channel in enumerate(threshold_channels):
                    # channel name is stored/derived in channel configuration message response and not under thresholds.
                    channel_name = phase_selector.channels[channel_index].channel_name
                    threshold_channel.channel_name = channel_name
        except TimeoutError:
            raise TimeoutError
        except Exception as e:
            logging.error(f"Exception in PhaseSelectorBuilder build {e}")
            raise Exception
        return phase_selector
