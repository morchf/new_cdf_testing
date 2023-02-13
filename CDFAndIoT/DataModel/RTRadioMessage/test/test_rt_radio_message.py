import base64
from random import randint

from gtt.data_model.rt_radio_message.rt_radio_message import RTRadioMessage


def random_uint(size: int):
    return randint(0, pow(2, size) - 1)


def random_int(size: int):
    magnitude = pow(2, size - 1)
    return randint(-magnitude, magnitude - 1)


def test_pack():
    veh_sn = random_uint(32)
    veh_rssi = random_uint(16)
    veh_gps_lat_ddmmmmmm = random_int(32)
    veh_gps_lon_dddmmmmmm = random_int(32)
    veh_gps_vel_mpsd5 = random_uint(8)
    veh_gps_hdg_deg2 = random_uint(8)
    veh_gps_cstat = random_uint(16)
    veh_gps_satellites = random_uint(32)
    veh_veh_id = random_uint(16)
    veh_city_id = random_uint(8)
    veh_mode_op_turn = random_uint(8)
    veh_class = random_uint(8)
    conditional_priority = random_uint(8)
    veh_diag_value = random_uint(32)

    expectedBytes = (
        b""
        + veh_sn.to_bytes(4, "little")
        + veh_rssi.to_bytes(2, "little")
        + b"\x00\x00"
        + veh_gps_lat_ddmmmmmm.to_bytes(4, "little", signed=True)
        + veh_gps_lon_dddmmmmmm.to_bytes(4, "little", signed=True)
        + veh_gps_vel_mpsd5.to_bytes(1, "little")
        + veh_gps_hdg_deg2.to_bytes(1, "little")
        + veh_gps_cstat.to_bytes(2, "little")
        + veh_gps_satellites.to_bytes(4, "little")
        + veh_veh_id.to_bytes(2, "little")
        + veh_city_id.to_bytes(1, "little")
        + veh_mode_op_turn.to_bytes(1, "little")
        + veh_class.to_bytes(1, "little")
        + conditional_priority.to_bytes(1, "little")
        + b"\x00\x00"
        + veh_diag_value.to_bytes(4, "little")
    )

    rt_msg = RTRadioMessage(
        veh_sn=veh_sn,
        veh_rssi=veh_rssi,
        veh_gps_lat_ddmmmmmm=veh_gps_lat_ddmmmmmm,
        veh_gps_lon_dddmmmmmm=veh_gps_lon_dddmmmmmm,
        veh_gps_vel_mpsd5=veh_gps_vel_mpsd5,
        veh_gps_hdg_deg2=veh_gps_hdg_deg2,
        veh_gps_cstat=veh_gps_cstat,
        veh_gps_satellites=veh_gps_satellites,
        veh_veh_id=veh_veh_id,
        veh_city_id=veh_city_id,
        veh_mode_op_turn=veh_mode_op_turn,
        veh_class=veh_class,
        conditional_priority=conditional_priority,
        veh_diag_value=veh_diag_value,
    )

    assert rt_msg.pack(byte_order="little") == expectedBytes


def test_unpack():
    veh_sn = random_uint(32)
    veh_rssi = random_uint(16)
    veh_gps_lat_ddmmmmmm = random_int(32)
    veh_gps_lon_dddmmmmmm = random_int(32)
    veh_gps_vel_mpsd5 = random_uint(8)
    veh_gps_hdg_deg2 = random_uint(8)
    veh_gps_cstat = random_uint(16)
    veh_gps_satellites = random_uint(32)
    veh_veh_id = random_uint(16)
    veh_city_id = random_uint(8)
    veh_mode_op_turn = random_uint(8)
    veh_class = random_uint(8)
    conditional_priority = random_uint(8)
    veh_diag_value = random_uint(32)

    msg_bytes = (
        b""
        + veh_sn.to_bytes(4, "little")
        + veh_rssi.to_bytes(2, "little")
        + b"\x00\x00"
        + veh_gps_lat_ddmmmmmm.to_bytes(4, "little", signed=True)
        + veh_gps_lon_dddmmmmmm.to_bytes(4, "little", signed=True)
        + veh_gps_vel_mpsd5.to_bytes(1, "little")
        + veh_gps_hdg_deg2.to_bytes(1, "little")
        + veh_gps_cstat.to_bytes(2, "little")
        + veh_gps_satellites.to_bytes(4, "little")
        + veh_veh_id.to_bytes(2, "little")
        + veh_city_id.to_bytes(1, "little")
        + veh_mode_op_turn.to_bytes(1, "little")
        + veh_class.to_bytes(1, "little")
        + conditional_priority.to_bytes(1, "little")
        + b"\x00\x00"
        + veh_diag_value.to_bytes(4, "little")
    )

    # With plain bytes
    rt_msg = RTRadioMessage.unpack(msg_bytes, byte_order="little")

    for key, value in rt_msg.dict().items():
        assert locals()[key] == value

    # With base64 str
    base64_msg = base64.encodebytes(msg_bytes).decode("ascii")
    rt_msg = RTRadioMessage.unpack(base64_msg, byte_order="little")

    for key, value in rt_msg.dict().items():
        assert locals()[key] == value

    # With hex str
    hex_msg = msg_bytes.hex()
    rt_msg = RTRadioMessage.unpack(hex_msg, byte_order="little")

    for key, value in rt_msg.dict().items():
        assert locals()[key] == value
