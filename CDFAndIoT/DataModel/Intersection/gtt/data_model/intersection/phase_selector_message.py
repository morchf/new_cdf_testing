import binascii
import logging
import math
import struct
from abc import ABC
from datetime import datetime
from typing import Any, Iterable, List, Optional, Union

from .constants import TIME_ZONES
from .phase_selector import (
    ApproachMapEntry,
    ConfigurationProfile,
    OutputChannel,
    PhaseSelector,
    ThresholdChannel,
    TimeLocalizationDetails,
)
from .util import coordinate_to_min_degrees


def hex_string(struct_fmt: str, *values) -> str:
    """Convert struct format string and values to a hex string (big-endian)

    Args:
        struct_fmt (str): Format string from struct module. Prepends '>'

    Returns:
        str: Hex string
    """
    struct_fmt = f">{struct_fmt.strip('>')}"

    return str(binascii.hexlify(struct.pack(struct_fmt, *values)))[2:-1].upper()


def padded_hex_string(s: str, n: int, *, fill_char=" ", encoding="utf-16be") -> str:
    """Pad a string to a set size and return as hex string

    Args:
        s (str): String
        n (int): Size of padded string
        fill_char (str, optional): Char to fill space. Defaults to " ".
        encoding (str, optional): String encoding. Defaults to "utf-16be".

    Returns:
        str: _description_
    """
    if s is None:
        s = ""

    return str(binascii.hexlify(s.ljust(n, fill_char).encode(encoding)).upper())[2:-1]


def unpack_padded(
    struct_fmt: str, data: bytes, *, n_left: int = None, n_right: int = None
) -> List[Any]:
    """Unpack a byte string with offsets

    Args:
        struct_fmt (str): Format of data to unpack
        data (bytes): Byte string
        n_left (int, optional): Number of bytes padded on left. Defaults to None.
        n_right (int, optional): Number of bytes paded on right. Defaults to None. Left padding overrides right padding

    Returns:
        List[Any]: Unpacked data fields
    """
    struct_fmt = struct_fmt.strip(">")
    format_size = struct.calcsize(f">{struct_fmt}")

    left_padding = ""
    right_padding = ""

    if n_left is not None:
        left_padding = f"{n_left}x"

        n_right = len(data) - format_size - n_left

        if n_right < 0:
            raise ValueError(f"Right padding is less than 0 ({n_right})")

        if n_right == 0:
            right_padding = ""
        else:
            right_padding = f"{n_right}x"

    elif n_right is not None:
        right_padding = f"{n_right}x"

        n_left = len(data) - format_size - n_right

        if n_left < 0:
            raise ValueError(f"Left padding is less than 0 ({n_left})")

        if n_left == 0:
            left_padding = ""
        else:
            left_padding = f"{n_left}x"

    return struct.unpack(f">{left_padding}{struct_fmt}{right_padding}", data)


def fill(lst: List[Any], n: int, e: Optional[Any] = 0) -> List[Any]:
    """Fill a list with default values up to a specified length

    Args:
        lst (List[Any]): List
        n (int): Length of returned list
        e (Optional[Any], optional): Default value for missing elements. Defaults to 0.

    Returns:
        List[Any]: List with default values in missing indicies
    """
    return ([*(lst or [])] + ([n] * n))[0:n]


def convert_meters_to_feet(x):
    return x * 3.28084


def convert_feet_to_decimeters(x):
    return x * 0.3048 * 10


class PhaseSelectorMessage(ABC):
    """Byte-encoded message request and response formats and parser

    Header and trailer bytes are stacially defined

    Response format types

    | Type   | Size     | Range                   | Format |
    |--------|----------|-------------------------|--------|
    | UCHAR  | 8 bits   | 0..255                  | B      |
    | CHAR   | 8 bits   | -128..127               | c      |
    | CHAR[] | 8 bits[] | -128..127               | s      |
    | UTF16  | 16 bits  | 0..65535                | 2s     |
    | USHORT | 16 bits  | 0..65535                | H      |
    | SHORT  | 16 bits  | -32768..32767           | h      |
    | ULONG  | 32 bits  | 0..4294967295           | L      |
    | LONG   | 32 bits  | -2147483648..2147483647 | l      |

    Each message response format adds the header and trailer bytes

    """

    id: str
    request_size: Optional[int] = 10
    # Just the response UCHAR
    response_format: Optional[str] = "6xB4x"
    request_format: Optional[str] = None

    HEADER = 0x10
    WILDCARD_DEVICE_ID = 0xFF800000
    TRAILER = 0x1003
    REQUEST_TEMPLATE = ">{request_format}"
    RESPONSE_TEMPLATE = ">{response_format}"

    @classmethod
    def _add_dle_padding(cls, byte_string):
        temp = byte_string
        count = 1
        for i in range(1, len(byte_string) - 2):
            if byte_string[i] == 16:
                temp = temp[:count] + binascii.a2b_hex("10") + temp[count:]
                count += 1
            count += 1
        return temp

    @classmethod
    def _remove_dle_padding(cls, byte_string):
        temp = byte_string
        count = 1
        i = 1
        while count < len(temp) - 3:
            if temp[count] == 16 and temp[count + 1] == 16:
                byte_string = byte_string[:i] + byte_string[i + 1 :]
                count += 1
            count += 1
            i += 1
        return byte_string

    @classmethod
    def pack(
        cls,
        *,
        msg_id: Optional[int] = None,
        device_id: Optional[str] = None,
        request_size: Optional[int] = None,
        request_format: Optional[str] = None,
        data: Optional[Union[str, Iterable]] = None,
        # Can default to using phase selctor ID on all messages, if needed
        phase_selector: Optional[PhaseSelector] = None,
    ) -> bytes:

        """Create a new byte message"""
        if cls.__dict__.get("request") is not None and device_id is None:
            return cls.request

        if device_id is None:
            logging.debug("Using default device ID now")
            device_id = PhaseSelector.wildcard_device_id()

        if msg_id is None:
            msg_id = cls.id

        if data is None:
            data = ""
        # Manually created or pre-computed data
        elif isinstance(data, str):
            data = data
        elif request_format is not None or cls.request_format is not None:
            data = struct.pack(
                cls.REQUEST_TEMPLATE.format(
                    request_format=request_format or cls.request_format
                ),
                # Enforce iterable packing of data fields
                *data,
            ).hex()

        # Check-sum payload
        data = data.zfill((request_size or cls.request_size) - 10).upper()
        payload = f"{PhaseSelectorMessage.HEADER:X}{msg_id:02X}"
        payload += f"{device_id}{data}"

        checksum = sum(binascii.a2b_hex(payload)) % (2**16)

        # <Header><Message ID><Connected Device Identifier><Data><Checksum><Trailer>
        return cls._add_dle_padding(
            binascii.a2b_hex(f"{payload}{checksum:04X}{PhaseSelectorMessage.TRAILER:X}")
        )

    @classmethod
    def unpack(cls, data: bytes, response_format: Optional[str] = None) -> Any:
        """Parse a byte message

        Raises:
            Exception: Invalid response

        Returns:
            Any: Parsed dictionary of properties
        """
        # Verify checksum
        checksum = sum(data[: len(data) - 4])
        if checksum != int(
            binascii.b2a_hex(data)[
                len(binascii.b2a_hex(data)) - 8 : len(binascii.b2a_hex(data)) - 4
            ],
            16,
        ):
            logging.debug(f"Checksum mismatched for received data - {data}")

        try:
            data = cls._remove_dle_padding(data)
            struct_fmt = PhaseSelectorMessage.RESPONSE_TEMPLATE.format(
                response_format=response_format or cls.response_format
            )

            try:
                (response_code, *response_body) = unpack_padded(
                    struct_fmt, data, n_left=0
                )
                logging.debug(f"Response code: {response_code}")
            except Exception:
                return unpack_padded(struct_fmt, data, n_left=0)

        except Exception as e:
            raise Exception(f"Invalid response received from device: {e}")

        return (response_code, *response_body)


class GetUnitPropertiesMessage(PhaseSelectorMessage):
    id = 0x1F
    response_format = "7xB10s9s9s10s9s9s16s10s16s9s16s16s16s16sll"

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        return super().pack(data="A1")

    @classmethod
    def unpack(cls, data):
        (
            rsp,
            serial_number,
            firmware_version,
            bootloader_firmware_version,
            aip_sn,
            aip_firmware_version,
            aip_bootloader_firmware_verison,
            radio_module_model,
            radio_module_sn,
            radio_firmware_version,
            radio_bootloader_version,
            gps_band,
            gps_firmware_revision,
            rf_module_sn,
            rf_module_version,
            latitude,
            longitude,
        ) = super().unpack(data)

        latitude = (
            0
            if latitude == 0
            else (
                (int(abs(latitude) / 1000000) + (abs(latitude) % 1000000) / 600000)
                * (latitude / abs(latitude))
            )
        )
        longitude = (
            0
            if longitude == 0
            else (
                (int(abs(longitude) / 1000000) + (abs(longitude) % 1000000) / 600000)
                * (longitude / abs(longitude))
            )
        )

        return {
            "latitude": round(float(latitude), 6),
            "longitude": round(float(longitude), 6),
            "firmware_version": firmware_version.decode(),
            "serial_number": serial_number.decode(),
        }


class GetGpsLocationMessage(PhaseSelectorMessage):
    id = 0x0C
    request_size = 10


class PingMessage(PhaseSelectorMessage):
    id = 0x11
    request_size = 10

    @classmethod
    def unpack(cls, data):
        (
            rsp,
            model_code,
            serial_number,
            rev1,
            rev2,
            rev3,
            month,
            day,
            year,
            hours,
            minutes,
            seconds,
            status,
        ) = unpack_padded("BB10s5s5s5sBBBBBBH", data, n_left=6)

        status = bin(status)[2:].zfill(16)
        operation_mode = status[:4]

        if operation_mode == "0000":
            operation_mode = "Online/Normal"
            status = "Normal"
        elif operation_mode == "0100":
            status = "Warning"
            operation_mode = "Initializing"
        elif operation_mode == "1000":
            status = "Error"
            operation_mode = "Broken"
        elif operation_mode == "1100":
            status = "Error"
            operation_mode = "Offline/Diagnostic"
        elif operation_mode == "0010":
            status = "Error"
            operation_mode = "Standby"
        elif operation_mode == "0001":
            status = "Warning"
            operation_mode = "Boot Mode"
        else:
            status = "Error"
            operation_mode = ""
        make, model = "", ""
        if model_code == 47:
            make = "GTT"
            model = "V764"

        return {
            "serial_number": serial_number,
            "status": status,
            "make": make,
            "model": model,
            "operation_mode": operation_mode,
        }


class GetMacAddressMessage(PhaseSelectorMessage):
    id = 0x04
    request_size = 10

    @classmethod
    def unpack(cls, data):
        mac_address = unpack_padded("6c", data, n_left=7)
        mac_address_str = ""
        for addr in mac_address:
            mac_address_str += binascii.b2a_hex(addr).decode("ascii")
        unit_id = (
            hex(int("800000", 16) | int(mac_address_str[-6:], 16))
            .replace("0x", "")
            .upper()
        )
        return {"mac_address": mac_address_str.upper(), "unit_id": unit_id}


class GetDeviceNameMessage(PhaseSelectorMessage):
    id = 0x20
    response_format = "6xB80s4x"

    @classmethod
    def unpack(cls, data):
        (rsp, encoded_name) = super().unpack(data)

        try:
            return {
                "device_name": encoded_name.rstrip(b"\x000").decode("utf-16be").strip()
            }
        except Exception:
            return {
                "device_name": encoded_name.rstrip(b"\x000").decode("utf-16").strip()
            }


class GetConfigurationDateTimeMessage(PhaseSelectorMessage):
    id = 0x1A
    request_size = 10

    @classmethod
    def unpack(cls, data):
        response_format = "6xBBBHBBB" + str(len(data) - 14) + "x"
        (response, month, day, year, hours, minutes, seconds) = super().unpack(
            data, response_format=response_format
        )
        time_string = f"{month} {day} {year} {hours} {minutes} {seconds}"
        if month and day and year:
            last_configured = datetime.strptime(time_string, "%m %d %Y %H %M %S")
        else:
            last_configured = datetime(1900, 1, 1)
        return {"last_configured": last_configured}


class GetTimeAndDateMessage(PhaseSelectorMessage):
    """Retrieve the Connected Device's date and time"""

    id = 0x1E

    @classmethod
    def unpack(cls, data: bytes):
        (rsp, month, date, year, hours, minutes, seconds) = super().unpack(data)

        return {
            "month": month,
            "date": date,
            "year": year,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
        }


class SetDateAndTimeMessage(PhaseSelectorMessage):
    """Set a Connected Device's date and time"""

    id = 0x1D

    @classmethod
    def pack(cls, phase_selector: PhaseSelector) -> bytes:
        today = datetime.now()

        data = (
            today.month,
            today.date,
            today.year,
            today.hour,
            today.minute,
            today.second,
        )

        return cls.pack(data=data)


class SetModemInitializationMessage(PhaseSelectorMessage):
    id = 0x01


class GetModemInitializationMessage(PhaseSelectorMessage):
    id = 0x02


class FirmwareUpgradeMessage(PhaseSelectorMessage):
    id = 0x05


class GetSerialAddressMessage(PhaseSelectorMessage):
    id = 0x07


class SetSerialAddressMessage(PhaseSelectorMessage):
    id = 0x08


class EnterPasswordMessage(PhaseSelectorMessage):
    id = 0x09


class ChangePasswordMessage(PhaseSelectorMessage):
    id = 0x0A


class SpecialModesMessage(PhaseSelectorMessage):
    id = 0x0D


class DiagnosticCommandMessage(PhaseSelectorMessage):
    id = 0x0E


class GetSerialCommunicationConfigurationMessage(PhaseSelectorMessage):
    id = 0x12


class SetSerialCommunicationConfigurationMessage(PhaseSelectorMessage):
    id = 0x13


class SetNetworkConfigurationMessage(PhaseSelectorMessage):
    id = 0x14


class GetNetworkConfigurationMessage(PhaseSelectorMessage):
    id = 0x15


class GetNetworkStatisticsMessage(PhaseSelectorMessage):
    id = 0x16


class SetConfirmationLightConfigurationMessage(PhaseSelectorMessage):
    id = 0x18


class GetConfirmationLightConfigurationMessage(PhaseSelectorMessage):
    id = 0x19


class GetConfigurationDateMessage(PhaseSelectorMessage):
    id = 0xE


class GetTimeLocalizationConfigurationMessage(PhaseSelectorMessage):
    id = 0x1B

    @classmethod
    def unpack(cls, data):
        response_format = "6xB240sh2BH5BH3B" + str(len(data) - 263) + "x"
        (
            resp_code,
            time_zone_string,
            utc_offset,
            forward_dst_month,
            forward_dst_date,
            forward_dst_year,
            forward_dst_hours,
            forward_dst_minutes,
            forward_dst_rule,
            reverse_dst_month,
            reverse_dst_date,
            reverse_dst_year,
            reverse_dst_hours,
            reverse_dst_minutes,
            reverse_dst_rule,
        ) = super().unpack(data, response_format=response_format)

        time_zone_string = time_zone_string.decode("utf-16be")

        timezone = ""
        for i in time_zone_string.split(" "):
            if i:
                timezone += i[0]

        get_time_localization = TimeLocalizationDetails(
            timezone=time_zone_string,
            utc_offset=utc_offset,
            forward=TimeLocalizationDetails.Date(
                month=forward_dst_month,
                date=forward_dst_date,
                year=forward_dst_year,
                hours=forward_dst_hours,
                minutes=forward_dst_minutes,
                rule=forward_dst_rule,
            ),
            reverse=TimeLocalizationDetails.Date(
                month=reverse_dst_month,
                date=reverse_dst_date,
                year=reverse_dst_year,
                hours=reverse_dst_hours,
                minutes=reverse_dst_minutes,
                rule=reverse_dst_rule,
            ),
        )

        return {
            "time_localization_details": get_time_localization,
            "timezone": timezone,
        }


class GetTimeandDateMessage(PhaseSelectorMessage):
    id = 0x1E


class GetChannelConfigurationMessage(PhaseSelectorMessage):
    id = 0x23
    request_format = "BB"

    @classmethod
    def pack(cls, *_, **__):
        messages = []
        for channel in [0x0, 0x1, 0x2, 0x3]:
            messages.append(super().pack(data=f"A7{channel:02X}"))
        return messages

    @classmethod
    def unpack(cls, data):
        skip = 6
        (
            resp_code,
            format_version,
            channel,
            logical_channel,
            channel_name,
        ) = unpack_padded("BBBB80s", data, n_left=skip)

        skip += 84

        channel_name = channel_name.decode().replace("\x00", "").strip()

        phases = (0) * 3
        (phases) = unpack_padded("3L", data, n_left=skip)
        phases = tuple(phases)

        skip += 12

        (high_priority_preempts) = unpack_padded("3B", data, n_left=skip)
        high_priority_preempts = tuple(high_priority_preempts)

        skip += 3

        (low_priority_preempts) = unpack_padded("3B", data, n_left=skip)

        skip += 3

        (low_priority_queue_jump_preempt,) = unpack_padded("B", data, n_left=skip)

        skip += 1

        (assigned_approaches) = unpack_padded("10B", data, n_left=skip)
        assigned_approaches = tuple(assigned_approaches)

        skip += 10

        (check_in_check_out_enabled,) = unpack_padded("B", data, n_left=skip)

        skip += 1

        (check_in_classes) = unpack_padded("16B", data, n_left=skip)
        check_in_classes = tuple(check_in_classes)
        skip += 16

        (
            check_in_entry_distance_threshold,
            check_in_exit_distance_threshold,
        ) = unpack_padded("HH", data, n_left=skip)

        skip += 4

        (check_in_announcement_output) = unpack_padded("3B", data, n_left=skip)
        check_in_announcement_output = tuple(check_in_announcement_output)

        skip += 3

        (
            check_out_entry_threshold,
            forward_calls_in_forward_direction,
        ) = unpack_padded("HB", data, n_left=skip)

        skip += 3

        (priority_outputs) = unpack_padded("".join(93 * ["B"]), data, n_left=skip)

        skip += 93

        (ignore_heading, *preempt_plan_evp) = unpack_padded("B3B", data, n_left=skip)

        skip += 4

        (*priority_plan_tsp,) = unpack_padded("3B", data, n_left=skip)
        return {
            "channels": [
                OutputChannel(
                    channel=channel,
                    channel_name=channel_name,
                    logical_channel=logical_channel,
                    format_version=format_version,
                    phases=phases,
                    high_priority_preempts=high_priority_preempts,
                    low_priority_preempts=low_priority_preempts,
                    low_priority_queue_jump_preempt=low_priority_queue_jump_preempt,
                    assigned_approaches=assigned_approaches,
                    check_in_check_out_enabled=check_in_check_out_enabled,
                    check_in_classes=check_in_classes,
                    check_in_entry_distance_threshold=check_in_entry_distance_threshold,
                    check_in_exit_distance_threshold=check_in_exit_distance_threshold,
                    check_in_announcement_output=check_in_announcement_output,
                    check_out_entry_threshold=check_out_entry_threshold,
                    forward_calls_in_forward_direction=forward_calls_in_forward_direction,
                    ignore_heading=ignore_heading,
                    preempt_plan_evp=preempt_plan_evp,
                    priority_plan_tsp=priority_plan_tsp,
                    priority_outputs=priority_outputs,
                )
            ]
        }


class GetApproachMapMessage(PhaseSelectorMessage):
    id = 0x25

    @classmethod
    def pack(cls, *_, **__):
        return super().pack(msg_id=0x25, data="000004001E")

    @classmethod
    def unpack(cls, data):
        skip = 6

        (
            resp_code,
            total_approaches,
            approach_offset,
            no_of_approaches,
        ) = unpack_padded("BBBB", data, n_left=skip)

        skip += 4

        approach_map_entries = []
        for i in range(no_of_approaches):
            (approach_name,) = unpack_padded("80s", data, n_left=skip)

            approach_name_str = ""
            for i in approach_name:
                if i and not (i == 2):
                    approach_name_str += chr(i)
            approach_name_str = approach_name_str.strip()

            skip += 80

            (no_of_coordinates,) = unpack_padded("B", data, n_left=skip)

            skip += 1

            coordinates = []
            for _ in range(no_of_coordinates):
                (x, y, width) = unpack_padded("hhB", data, n_left=skip)

                skip += 5

                coordinates.append(ApproachMapEntry.Coordinate(x=x, y=y, width=width))

            approach_map_entries.append(
                ApproachMapEntry(
                    approach_name=approach_name_str,
                    number_of_coordinates=no_of_coordinates,
                    coordinates=coordinates,
                )
            )

        return {
            "approach_map": approach_map_entries,
            "approach_offset": approach_offset,
        }


class GetMapGeographyPointsMessage(PhaseSelectorMessage):
    id = 0x26


class SetMapGeographyPointsMessage(PhaseSelectorMessage):
    id = 0x27


class SetTimePlanCalendarMessage(PhaseSelectorMessage):
    id = 0x28


class GetTimePlanCalendarMessage(PhaseSelectorMessage):
    id = 0x29


class SetDailyScheduleMessage(PhaseSelectorMessage):
    id = 0x2A


class GetDailyScheduleMessage(PhaseSelectorMessage):
    id = 0x2B


class GetConfigurationProfileMessage(PhaseSelectorMessage):
    id = 0x2D
    request_format = "BBB"

    @classmethod
    def pack(cls, *_, **__):
        return super().pack(data="0001A4")

    @classmethod
    def unpack(cls, data):
        skip = 91

        (
            resp_code,
            format_version,
            profile_type,
            profile_index,
            profile_name,
            number_of_high_codes,
        ) = unpack_padded("BBBB80sB", data, n_left=6)

        profile_name = profile_name.decode("utf-16be").strip("\0")

        high_codes = ""
        if number_of_high_codes > 0:
            (high_codes, number_of_low_codes) = unpack_padded(
                f"{number_of_high_codes * 8}sB", n_left=skip
            )
        else:
            (number_of_low_codes,) = unpack_padded("B", data, n_left=skip)

        skip += number_of_high_codes * 8 + 1

        low_codes = ""
        if number_of_low_codes > 0:
            (low_codes, high_priority_relative_priorities_enabled) = unpack_padded(
                f"{number_of_low_codes * 8}sB", data, n_left=skip
            )
        else:
            (high_priority_relative_priorities_enabled,) = unpack_padded(
                "B", data, n_left=skip
            )

        skip += number_of_low_codes * 8 + 1

        (high_priority_relative_priorities) = unpack_padded("16B", data, n_left=skip)

        skip += 16

        (low_priority_relative_priorities_enabled,) = unpack_padded(
            "B", data, n_left=skip
        )

        skip += 1

        (low_priority_relative_priorities) = unpack_padded("16B", data, n_left=skip)

        skip += 16

        (
            relative_priority_lockout_eta,
            conditional_priority_enabled,
            number_of_channels,
        ) = unpack_padded("BBB", data, n_left=skip)

        skip += 3

        threshold_channels = []
        for channel_id in range(number_of_channels):
            (
                channel,
                high_priority_preempt_enabled,
                low_priority_preempt_enabled,
                high_priority_directional_priority,
                low_priority_directional_priority,
                call_bridging_enabled,
                call_bridging_time,
                low_priority_reservice_enabled,
                low_priority_reservice_time,
                high_priority_maximum_call_time,
                low_priority_maximum_call_time,
                high_priority_call_hold_time,
                low_priority_call_hold_time,
                high_priority_call_delay_time,
                low_priority_call_delay_time,
                high_priority_off_approach_hold_time,
                low_priority_off_approach_hold_time,
            ) = unpack_padded("BBBBBBBBBHHHHBBBB", data, n_left=skip)

            skip += 21

            high_priority_primary_intensity_thresholds = unpack_padded(
                "16H", data, n_left=skip
            )

            skip += 32

            low_priority_primary_intensity_thresholds = unpack_padded(
                "16H", data, n_left=skip
            )

            skip += 32

            high_priority_auxiliary_intensity_thresholds = unpack_padded(
                "16H", data, n_left=skip
            )

            skip += 32

            low_priority_auxiliary_intensity_thresholds = unpack_padded(
                "16H", data, n_left=skip
            )

            skip += 32

            high_priority_eta_thresholds = unpack_padded("16B", data, n_left=skip)

            skip += 16

            low_priority_eta_thresholds = unpack_padded("16B", data, n_left=skip)

            skip += 16

            high_priority_distance_thresholds = unpack_padded("16H", data, n_left=skip)
            high_priority_distance_thresholds = [
                round(
                    convert_meters_to_feet(
                        high_priority_distance_thresholds[index] / 10
                    )
                )
                for index in range(len(high_priority_distance_thresholds))
            ]
            high_priority_distance_thresholds = tuple(high_priority_distance_thresholds)
            skip += 32

            low_priority_distance_thresholds = unpack_padded("16H", data, n_left=skip)
            low_priority_distance_thresholds = [
                round(
                    convert_meters_to_feet(low_priority_distance_thresholds[index] / 10)
                )
                for index in range(len(low_priority_distance_thresholds))
            ]
            low_priority_distance_thresholds = tuple(low_priority_distance_thresholds)
            skip += 32

            (proximity_threshold,) = unpack_padded("H", data, n_left=skip)

            skip += 2

            threshold_channels.append(
                ThresholdChannel(
                    priority=None,
                    channel=channel,
                    call_bridging_enabled=call_bridging_enabled,
                    call_bridging_time=call_bridging_time,
                    proximity_threshold=proximity_threshold,
                    high_priority=ThresholdChannel.HighPriorityChannel(
                        max_call_time=high_priority_maximum_call_time,
                        call_hold_time=high_priority_call_hold_time,
                        preempt_enabled=high_priority_preempt_enabled,
                        directional_priority=high_priority_directional_priority,
                        call_delay_time=high_priority_call_delay_time,
                        off_approach_hold_time=high_priority_off_approach_hold_time,
                        primary_intensity_thresholds=high_priority_primary_intensity_thresholds,
                        auxiliary_intensity_thresholds=high_priority_auxiliary_intensity_thresholds,
                        eta_thresholds=high_priority_eta_thresholds,
                        distance_thresholds=high_priority_distance_thresholds,
                    ),
                    low_priority=ThresholdChannel.LowPriorityChannel(
                        max_call_time=low_priority_maximum_call_time,
                        call_hold_time=low_priority_call_hold_time,
                        preempt_enabled=low_priority_preempt_enabled,
                        directional_priority=low_priority_directional_priority,
                        call_delay_time=low_priority_call_delay_time,
                        off_approach_hold_time=low_priority_off_approach_hold_time,
                        primary_intensity_thresholds=low_priority_primary_intensity_thresholds,
                        auxiliary_intensity_thresholds=low_priority_auxiliary_intensity_thresholds,
                        eta_thresholds=low_priority_eta_thresholds,
                        distance_thresholds=low_priority_distance_thresholds,
                        reservice_enabled=low_priority_reservice_enabled,
                        reservice_time=low_priority_reservice_time,
                    ),
                )
            )

        # TODO: Check skipping 192 bytes in each channel
        return {
            "configuration_profile": ConfigurationProfile(
                format_version=format_version,
                profile_type=profile_type,
                profile_index=profile_index,
                profile_name=profile_name,
                number_of_high_codes=number_of_high_codes,
                number_of_low_codes=number_of_low_codes,
                high_priority_relative_priorities_enabled=high_priority_relative_priorities_enabled,
                high_priority_relative_priorities=high_priority_relative_priorities,
                low_priority_relative_priorities_enabled=low_priority_relative_priorities_enabled,
                low_priority_relative_priorities=low_priority_relative_priorities,
                relative_priority_lockout_eta=relative_priority_lockout_eta,
                conditional_priority_enabled=conditional_priority_enabled,
                number_of_channels=number_of_channels,
                channels=threshold_channels,
                high_codes=high_codes,
                low_code=low_codes,
            )
        }


class GetValidCodesMessage(PhaseSelectorMessage):
    id = 0x2E


class SetValidCodesMessage(PhaseSelectorMessage):
    id = 0x2F


class SetBaseStationParametersMessage(PhaseSelectorMessage):
    id = 0x30


class GetBaseStationParametersMessage(PhaseSelectorMessage):
    id = 0x31


class EvacuationModeMessage(PhaseSelectorMessage):
    id = 0x32


class GetRadioChannelMessage(PhaseSelectorMessage):
    id = 0x33


class SetRadioChannelMessage(PhaseSelectorMessage):
    id = 0x34


class GetControllerTimeSyncMessage(PhaseSelectorMessage):
    id = 0x35


class SetControllerTimeSyncMessage(PhaseSelectorMessage):
    id = 0x36


class GetControllerTimeSyncInputConfigurationMessage(PhaseSelectorMessage):
    id = 0x37


class SetControllerTimeSyncInputConfigurationMessage(PhaseSelectorMessage):
    id = 0x38


class GetDelawareModeConfigurationMessage(PhaseSelectorMessage):
    id = 0x39


class SetDelawareModeConfigurationMessage(PhaseSelectorMessage):
    id = 0x3A


class SetTimePlanWeekMessage(PhaseSelectorMessage):
    id = 0x3B


class GetTimePlanWeekMessage(PhaseSelectorMessage):
    id = 0x3C


class SetLowPriorityOutputModeandStateMessage(PhaseSelectorMessage):
    id = 0x3D


class GetLowPriorityOutputModeandStateMessage(PhaseSelectorMessage):
    id = 0x3E


class GetActivityLogMessage(PhaseSelectorMessage):
    id = 0x40


class SetActivityLogFiltersMessage(PhaseSelectorMessage):
    id = 0x41


class GetActivityLogFiltersMessage(PhaseSelectorMessage):
    id = 0x42


class GetCallPlaybackLogMessage(PhaseSelectorMessage):
    id = 0x43


class GetPlaybackLogDirectoryMessage(PhaseSelectorMessage):
    id = 0x44


class GetTSPGreenTimeLogMessage(PhaseSelectorMessage):
    id = 0x45


class GetPreemptGreenTimeLogMessage(PhaseSelectorMessage):
    id = 0x46


class GetGreenCycleLogMessage(PhaseSelectorMessage):
    id = 0x47


class SetGreenSenseLoggingConfigurationMessage(PhaseSelectorMessage):
    id = 0x48


class GetGreenSenseLoggingConfigurationMessage(PhaseSelectorMessage):
    id = 0x49


class MQTTBrokerEndpointConfigurationMessage(PhaseSelectorMessage):
    id = 0x4A


class MQTTCredentialConfigurationMessage(PhaseSelectorMessage):
    id = 0x4B


class UpdateRadioModuleFirmwareImageMessage(PhaseSelectorMessage):
    id = 0x4C


class MQTTWriteTLSCredentialsMessage(PhaseSelectorMessage):
    id = 0x4D


class ClearNonVolatileMemoryMessage(PhaseSelectorMessage):
    id = 0x4E


class ResetHardwareMessage(PhaseSelectorMessage):
    id = 0x4F


class GetPowerUpDiagnosticResultsMessage(PhaseSelectorMessage):
    id = 0x50


class GetPhaseStatusMessage(PhaseSelectorMessage):
    id = 0x51


class GetTrackingStatusMessage(PhaseSelectorMessage):
    id = 0x52


class SetOperatingModeMessage(PhaseSelectorMessage):
    id = 0x54


class GetPreemptionOutputsStatusMessage(PhaseSelectorMessage):
    id = 0x55


class GetDetectorStatusMessage(PhaseSelectorMessage):
    id = 0x56


class GetDiagnosticsLogMessage(PhaseSelectorMessage):
    id = 0x57


class GetMaintenanceLogMessage(PhaseSelectorMessage):
    id = 0x58


class GetPreemptionStatusMessage(PhaseSelectorMessage):
    id = 0x59


class GetVehiclesHeardStatusMessage(PhaseSelectorMessage):
    id = 0x5A


class GetIntersectionsHeardStatusMessage(PhaseSelectorMessage):
    id = 0x5B


class NetworkPreemptionRequestMessage(PhaseSelectorMessage):
    id = 0x5C


class NetworkVehiclePositionUpdateMessage(PhaseSelectorMessage):
    id = 0x5D


class GetGPSStatusMessage(PhaseSelectorMessage):
    id = 0x5E


class NetworkDetectedCallMessage(PhaseSelectorMessage):
    id = 0x5F


class SetNTCIP1211ConfigurationMessage(PhaseSelectorMessage):
    id = 0x60


class GetNTCIP1211ConfigurationMessage(PhaseSelectorMessage):
    id = 0x61


class CompleteGPSModuleFirmwareImageMessage(PhaseSelectorMessage):
    id = 0x62


class QueryGPSModuleFirmwareImageStatusMessage(PhaseSelectorMessage):
    id = 0x63


class UpdateGPSModuleFirmwareImageMessage(PhaseSelectorMessage):
    id = 0x64


class StartNewGPSModuleFirmwareImageMessage(PhaseSelectorMessage):
    id = 0x65


class OpenAIPPartitionMessage(PhaseSelectorMessage):
    id = 0x66


class WriteAIPPartitionBlockMessage(PhaseSelectorMessage):
    id = 0x67


class QueryOpenAIPPartitionMessage(PhaseSelectorMessage):
    id = 0x68


class CloseAIPPartitionMessage(PhaseSelectorMessage):
    id = 0x69


class PerformRadio1TestMessage(PhaseSelectorMessage):
    id = 0x6D


class PerformRadio2TestMessage(PhaseSelectorMessage):
    id = 0x6E


class GetIntersectionRadio1TestDataMessage(PhaseSelectorMessage):
    id = 0x6F


class GetGPSFilterDataMessage(PhaseSelectorMessage):
    id = 0x70


class EnableleDisableGPSFilteringMessage(PhaseSelectorMessage):
    id = 0x71


class SetRangeTimeoutMessage(PhaseSelectorMessage):
    id = 0x72


class GetRangeTimeoutMessage(PhaseSelectorMessage):
    id = 0x73


class GetInfraredTestMeasurementsMessage(PhaseSelectorMessage):
    id = 0x74


class UIFCommandMessage(PhaseSelectorMessage):
    id = 0x75


class SetDSRCIntersectionMapMessage(PhaseSelectorMessage):
    id = 0x76


class GetDSRCIntersectionMapMessage(PhaseSelectorMessage):
    id = 0x77


class SetDSRCRadioConfigMessage(PhaseSelectorMessage):
    id = 0x78


class GetDSRCRadioConfigMessage(PhaseSelectorMessage):
    id = 0x79


class SetNetworkUDPConfigurationMessage(PhaseSelectorMessage):
    id = 0x7A


class GetNetworkUDPConfigurationMessage(PhaseSelectorMessage):
    id = 0x7B


class SetActiveCallNotificationConfigurationMessage(PhaseSelectorMessage):
    id = 0x7C


class GetActiveCallNotificationConfigurationMessage(PhaseSelectorMessage):
    id = 0x7D


READ_MESSAGES = [
    PingMessage,
    GetMacAddressMessage,
    GetDeviceNameMessage,
    GetTimeLocalizationConfigurationMessage,
    GetApproachMapMessage,
    GetUnitPropertiesMessage,
    GetChannelConfigurationMessage,
    GetConfigurationProfileMessage,
    GetConfigurationDateTimeMessage,
]


class SetDeviceNameMessage(PhaseSelectorMessage):
    id = 0x21
    request_size = 90
    request_format = "80s"

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        device_name = phase_selector.device_name

        # Add right-padding
        data = padded_hex_string(device_name, 40, fill_char=" ")

        return super().pack(data=data)


class SetGpsLocationMessage(PhaseSelectorMessage):
    id = 0x0B
    request_size = 18
    request_format = "ll"

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        latitude = coordinate_to_min_degrees(phase_selector.latitude or 0)
        longitude = coordinate_to_min_degrees(phase_selector.longitude or 0)

        return super().pack(data=[latitude, longitude])


class SetTimeLocalizationConfigurationMessage(PhaseSelectorMessage):
    id = 0x1C
    request_size = 266
    request_format = "240sh2BH3B2BH3B"

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        timezone = phase_selector.timezone
        timezone_info = TIME_ZONES[timezone]
        timezone_name = timezone_info["name"]
        timezone_data = timezone_info["data"]

        encoded_timezone = padded_hex_string(timezone_name, 120)

        data = f"{encoded_timezone}{timezone_data}"

        return super().pack(data=data)


class ClearApproachMapMessage(PhaseSelectorMessage):
    id = 0x24
    request_size = 13
    request_format = "3B"

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        operation = 0
        approach_offset = 0
        num_approaches = 0

        return super().pack(data=[operation, approach_offset, num_approaches])

    @classmethod
    def unpack(cls, data):
        return {}


class SetApproachMapMessage(PhaseSelectorMessage):
    id = 0x24

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        approaches = phase_selector.approach_map or []

        operation = 7
        approach_offset = 0
        num_approaches = 0 if approaches is None else len(approaches)

        data = hex_string("3B", operation, approach_offset, num_approaches)

        for approach_map in approaches:
            approach_name = approach_map.approach_name.replace("_", "").capitalize()

            data += padded_hex_string(approach_name, 40)

            num_coordinates = len(approach_map.coordinates)

            data += hex_string("B", num_coordinates)

            coordinates = approach_map.coordinates or []

            for approach_map_coordinates in coordinates:
                x = approach_map_coordinates.x
                y = approach_map_coordinates.y

                data += hex_string(
                    "h", int(math.copysign(32767, x)) if abs(x) >= 32767 else int(x)
                )
                data += hex_string(
                    "h", int(math.copysign(32767, y)) if abs(y) >= 32767 else int(y)
                )

                # Width is offset by 30 meters, so here zero equates to 30
                width = max(0, approach_map_coordinates.width - 30)

                data += hex_string("B", width)

        return super().pack(data=data)


class SaveApproachMapMessage(PhaseSelectorMessage):
    id = 0x24
    request_size = 13
    request_format = "3B"

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        operation = 2
        approach_offset = 0
        num_approaches = 0

        data = struct.pack("3B", operation, approach_offset, num_approaches).hex()

        return super().pack(data=data)


class SetConfigurationProfileMessage(PhaseSelectorMessage):
    id = 0x2C

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        cp = phase_selector.configuration_profile

        data = hex_string(
            "BBB",
            # 0: New data, format 1
            # 1: Reset
            # 2: New data, format 2
            # 3: New data, format 3
            # 4/5: New data, format 4
            5,
            cp.profile_type,
            cp.profile_index,
        )
        data += padded_hex_string(cp.profile_name, 40)

        data += hex_string("B", cp.number_of_high_codes)
        if cp.number_of_high_codes > 0:
            data += hex_string(
                f"B{cp.number_of_high_codes * 8}s",
                cp.number_of_high_codes,
            )

        data += hex_string("B", cp.number_of_low_codes)
        if cp.number_of_low_codes > 0:
            data += hex_string(
                f"B{cp.number_of_low_codes * 8}s",
                cp.number_of_low_codes,
            )

        data += hex_string("B", cp.high_priority_relative_priorities_enabled)
        data += hex_string("16B", *cp.high_priority_relative_priorities)
        data += hex_string("B", cp.low_priority_relative_priorities_enabled)
        data += hex_string("16B", *cp.low_priority_relative_priorities)

        data += hex_string(
            "BBB",
            cp.relative_priority_lockout_eta,
            cp.conditional_priority_enabled,
            cp.number_of_channels,
        )

        for i, channel in enumerate(cp.channels):
            channel_data = ""

            channel_data += hex_string("B", i)
            channel_data += hex_string("B", channel.high_priority.preempt_enabled)
            channel_data += hex_string("B", channel.low_priority.preempt_enabled)
            channel_data += hex_string("B", channel.high_priority.directional_priority)
            channel_data += hex_string("B", channel.low_priority.directional_priority)
            channel_data += hex_string("B", channel.call_bridging_enabled)
            channel_data += hex_string("B", channel.call_bridging_time)
            channel_data += hex_string("B", channel.low_priority.reservice_enabled)
            channel_data += hex_string("B", channel.low_priority.reservice_time)
            channel_data += hex_string("H", channel.high_priority.max_call_time)
            channel_data += hex_string("H", channel.low_priority.max_call_time)
            channel_data += hex_string("H", channel.high_priority.call_hold_time or 0)
            channel_data += hex_string("H", channel.low_priority.call_hold_time or 0)
            channel_data += hex_string("B", channel.high_priority.call_delay_time)
            channel_data += hex_string("B", channel.low_priority.call_delay_time)
            channel_data += hex_string(
                "B", channel.high_priority.off_approach_hold_time
            )
            channel_data += hex_string("B", channel.low_priority.off_approach_hold_time)
            channel_data += hex_string(
                "16H", *channel.high_priority.primary_intensity_thresholds
            )
            channel_data += hex_string(
                "16H", *channel.low_priority.primary_intensity_thresholds
            )
            channel_data += hex_string(
                "16H", *channel.high_priority.auxiliary_intensity_thresholds
            )
            channel_data += hex_string(
                "16H", *channel.low_priority.auxiliary_intensity_thresholds
            )
            channel_data += hex_string("16B", *channel.high_priority.eta_thresholds)
            channel_data += hex_string("16B", *channel.low_priority.eta_thresholds)
            channel.high_priority.distance_thresholds = [
                int(convert_feet_to_decimeters(x))
                for x in channel.high_priority.distance_thresholds
            ]
            channel_data += hex_string(
                "16H", *channel.high_priority.distance_thresholds
            )
            channel.low_priority.distance_thresholds = [
                int(convert_feet_to_decimeters(x))
                for x in channel.low_priority.distance_thresholds
            ]
            channel_data += hex_string("16H", *channel.low_priority.distance_thresholds)
            channel_data += hex_string("H", min(3200, channel.proximity_threshold))

            data += channel_data

        return super().pack(phase_selector=phase_selector, data=data)


class SetChannelConfigurationMessage(PhaseSelectorMessage):
    id = 0x22

    @classmethod
    def pack(cls, phase_selector: PhaseSelector):
        messages = []

        for i, channel in enumerate(phase_selector.channels or []):
            data = (
                "A7"
                if channel.format_version is None
                else hex_string("B", int(channel.format_version))
            )

            # Channel
            data += hex_string("B", i)
            # Logical channel
            data += hex_string("B", i)
            data += padded_hex_string(
                phase_selector.configuration_profile.channels[i].channel_name, 40
            )

            data += hex_string("3L", *fill(channel.phases, 3))
            data += hex_string("3B", *fill(channel.high_priority_preempts, 3))
            data += hex_string("3B", *fill(channel.low_priority_preempts, 3))
            data += hex_string("B", channel.low_priority_queue_jump_preempt or 0)
            data += hex_string("10B", *fill(channel.assigned_approaches, 10))
            data += hex_string("B", channel.check_in_check_out_enabled or 0)
            data += hex_string("16B", *fill(channel.check_in_classes, 16))
            data += hex_string("H", channel.check_in_entry_distance_threshold or 0)
            data += hex_string("H", channel.check_in_exit_distance_threshold or 0)
            data += hex_string("3B", *fill(channel.check_in_announcement_output, 3))
            data += hex_string("H", channel.check_out_entry_threshold or 0)
            data += hex_string("B", channel.forward_calls_in_forward_direction or 0)
            data += hex_string("".join("B" * 93), *fill(channel.priority_outputs, 93))
            data += hex_string("B", channel.ignore_heading or 0)
            data += hex_string("3B", *fill(channel.preempt_plan_evp, 3))
            data += hex_string("3B", *fill(channel.priority_plan_tsp, 3))

            messages.append(super().pack(data=data))

        return messages


WRITE_MESSAGES = [
    SetGpsLocationMessage,
    SetDeviceNameMessage,
    SetTimeLocalizationConfigurationMessage,
    SetConfigurationProfileMessage,
    SetChannelConfigurationMessage,
    ClearApproachMapMessage,
    SetApproachMapMessage,
]


RESET_MESSAGES = [ResetHardwareMessage]
