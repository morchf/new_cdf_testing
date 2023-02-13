import logging
from typing import ForwardRef, Optional

from pydantic import Field, root_validator

from .phase_selector import ConfigurationProfile, OutputChannel, PhaseSelector
from .util import merge

Intersection = ForwardRef("Intersection")


class Intersection(PhaseSelector):
    """Persisted intersection fields"""

    agency_id: Optional[str] = Field(alias="agencyId")
    intersection_id: Optional[str] = Field(alias="intersectionId")
    intersection_name: Optional[str] = Field(alias="intersectionName")
    ip_address: Optional[str] = Field(alias="ipAddress")
    port: Optional[int]

    @root_validator()
    def sync_device_name(cls, values):
        """Sync device and intersection name"""
        intersection_name = values.get("intersection_name")
        device_name = values.get("device_name")

        if intersection_name is not None:
            values.update(device_name=intersection_name)
            return values

        values.update(intersection_name=device_name)

        return values

    @root_validator()
    def sync_id(cls, values):
        """Sync ID and serial number"""
        intersection_id = values.get("intersection_id")
        serial_number = values.get("serial_number")

        if serial_number is None:
            values.update(serial_number=intersection_id)
            return values

        if intersection_id is None:
            values.update(intersection_id=serial_number)

        return values

    @classmethod
    def from_existing(
        cls,
        device_phase_selector: PhaseSelector,
        intersection: Intersection,
        cached_intersection: Optional[Intersection] = None,
    ) -> Intersection:
        configuration_profile = device_phase_selector.configuration_profile

        # Ignore differences in device and cached intersection
        # Use device only in place of missing cache
        if cached_intersection is not None:
            configuration_profile = ConfigurationProfile(
                **merge(
                    device_phase_selector.configuration_profile.dict(),
                    {}
                    if cached_intersection is None
                    else cached_intersection.configuration_profile.dict(),
                    overwrite=True,
                )
            )

        # Convert thresholds
        if configuration_profile is not None and intersection.thresholds is not None:
            thresholds = intersection.thresholds
            for low_priority_channel, high_priority_channel in zip(
                thresholds.low_priority,
                thresholds.high_priority,
            ):
                if (low_priority_channel.channel != high_priority_channel.channel) or (
                    low_priority_channel.channel_name
                    != high_priority_channel.channel_name
                ):
                    raise Exception("Channels not in order")

                channel = next(
                    filter(
                        lambda c: c.channel == low_priority_channel.channel,
                        configuration_profile.channels,
                    ),
                    None,
                )

                if channel is None:
                    logging.error("No matching channel")
                    continue

                channel.channel_name = low_priority_channel.channel_name

                # Overwrite low priority channel
                channel.low_priority.call_hold_time = (
                    low_priority_channel.call_hold_time
                )
                channel.low_priority.max_call_time = low_priority_channel.max_call_time

                channel.low_priority.eta_thresholds = []
                channel.low_priority.distance_thresholds = []
                for c in low_priority_channel.classes:
                    channel.low_priority.eta_thresholds.append(c.eta)
                    channel.low_priority.distance_thresholds.append(c.distance)

                # Overwrite high priority channel
                channel.high_priority.call_hold_time = (
                    high_priority_channel.call_hold_time
                )
                channel.high_priority.max_call_time = (
                    high_priority_channel.max_call_time
                )

                channel.high_priority.eta_thresholds = []
                channel.high_priority.distance_thresholds = []
                for c in high_priority_channel.classes:
                    channel.high_priority.eta_thresholds.append(c.eta)
                    channel.high_priority.distance_thresholds.append(c.distance)

        channels = device_phase_selector.channels

        if cached_intersection is not None and cached_intersection.channels is not None:
            channels = []
            for device_channel, cached_channel in zip(
                device_phase_selector.channels,
                (
                    cached_intersection.channels
                    or (len(cached_intersection.channels) * [{}])
                ),
            ):
                channels.append(
                    OutputChannel(
                        **merge(
                            device_channel.dict(),
                            {} if cached_channel is None else cached_channel.dict(),
                            overwrite=True,
                        )
                    )
                )

        # Convert outputs
        if channels is not None and intersection.outputs is not None:

            for low_priority_output, high_priority_output in zip(
                intersection.outputs.low_priority.channels,
                intersection.outputs.high_priority.channels,
            ):
                if low_priority_output.channel != high_priority_output.channel:
                    raise Exception("Output channels not in order")

                channel = next(
                    filter(
                        lambda c: c.channel == low_priority_output.channel, channels
                    ),
                    None,
                )

                if channel is None:
                    logging.error("No matching output channel")
                    continue

                # TODO: Set 'type'
                # intersection.outputs.low_priority.type
                # intersection.outputs.high_priority.type

                channel.preempt_plan_evp = (
                    high_priority_output.straight,
                    high_priority_output.left,
                    high_priority_output.right,
                )
                channel.priority_plan_tsp = (
                    low_priority_output.straight,
                    low_priority_output.left,
                    low_priority_output.right,
                )

        # Convert approach map
        approach_map = intersection.approach_map
        if intersection.approach_map is None:
            approach_map = (
                cached_intersection.approach_map
                if cached_intersection is not None
                else device_phase_selector.approach_map
            )

        return cls(
            **merge(
                merge(
                    device_phase_selector.dict(
                        exclude={"configuration_profile", "channels", "approach_map"}
                    ),
                    {}
                    if cached_intersection is None
                    else cached_intersection.dict(
                        exclude={"configuration_profile", "channels", "approach_map"}
                    ),
                    overwrite=True,
                ),
                intersection.dict(
                    exclude={
                        "configuration_profile",
                        "channels",
                        "outputs",
                        "thresholds",
                        "approach_map",
                    }
                ),
                overwrite=True,
            ),
            configuration_profile=configuration_profile,
            channels=channels,
            approach_map=approach_map
        )
