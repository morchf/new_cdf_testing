from gtt.data_model.rt_radio_message.gps_data import GPSData
from gtt.data_model.rt_radio_message.struct_model import (
    StructModel,
    pad,
    sint32,
    uint8,
    uint16,
    uint32,
)


class RTRadioMessage(StructModel):
    veh_sn: int = uint32()
    veh_rssi: int = uint16()
    padding_1: int = pad(2)
    veh_gps_lat_ddmmmmmm: int = sint32()
    veh_gps_lon_dddmmmmmm: int = sint32()
    veh_gps_vel_mpsd5: int = uint8()
    veh_gps_hdg_deg2: int = uint8()
    veh_gps_cstat: int = uint16()
    veh_gps_satellites: int = uint32()
    veh_veh_id: int = uint16()
    veh_city_id: int = uint8()
    veh_mode_op_turn: int = uint8()
    veh_class: int = uint8()
    conditional_priority: int = uint8()
    padding_2: int = pad(2)
    veh_diag_value: int = uint32()

    def gps_data(self) -> GPSData:
        latitude, longitude = GPSData.from_min_degrees(
            self.veh_gps_lat_ddmmmmmm, self.veh_gps_lon_dddmmmmmm
        )
        return GPSData(
            latitude=latitude,
            longitude=longitude,
            speed=self.veh_gps_vel_mpsd5 / 5,
            heading=self.veh_gps_hdg_deg2 * 2,
        )
