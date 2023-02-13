from typing import Any, Dict, Tuple

from pydantic import BaseModel, Field, NonNegativeFloat


class GPSData(BaseModel):
    """Pydantic Model to abstract the validation and (de)serialization of GPS data

    It contains the following properties:
       - latitude:  Degrees North, in the WGS-84 coordinate system
       - longitude: Degrees East, in the WGS-84 coordinate system
       - speed:     Momentary speed measured by the vehicle, in kilometers per hour
       - heading:   Degrees clockwise from North. This can be compass bearing or the
                    direction toward the next stop
    """

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: NonNegativeFloat
    heading: float = Field(ge=0, le=360)

    def lat_lon(self) -> str:
        lat = f"{self.latitude:.3f}"[:-1] + (
            "L" if abs(self.latitude) % 0.01 < 0.005 else "H"
        )
        lon = f"{self.longitude:.3f}"[:-1] + (
            "L" if abs(self.longitude) % 0.01 < 0.005 else "H"
        )
        return f"{lat},{lon}"

    def minute_degrees(self) -> Tuple[int, int]:
        lat_min_degrees = (
            f"{int(self.latitude):02}{int(abs(self.latitude) % 1 * 60 * 10_000):06}"
        )
        lon_min_degrees = (
            f"{int(self.longitude):03}{int(abs(self.longitude) % 1 * 60 * 10_000):06}"
        )
        return int(lat_min_degrees), int(lon_min_degrees)

    @classmethod
    def from_min_degrees(
        cls, lat_min_degrees: int, lon_min_degrees: int
    ) -> Tuple[float, float]:
        lat_whole_degrees = abs(lat_min_degrees) / 100_000
        lon_whole_degrees = abs(lon_min_degrees) / 100_000
        lat_decimal = abs(lat_min_degrees) % 100_000 / 60_000
        lon_decimal = abs(lon_min_degrees) % 100_000 / 60_000
        latitude = lat_whole_degrees + lat_decimal
        longitude = lon_whole_degrees + lon_decimal
        return (
            -latitude if lat_min_degrees < 0 else latitude,
            -longitude if lon_min_degrees < 0 else longitude,
        )

    @classmethod
    def from_rt_radio(
        cls,
        veh_gps_lat_ddmmmmmm: int,
        veh_gps_lon_dddmmmmmm: int,
        veh_gps_vel_mpsd5: int,
        veh_gps_hdg_deg5: int,
    ) -> "GPSData":
        """Does not necessarily return the original gps data that was used to
        form the RTRadio Message, as precision may be lost during the initial
        transformation"""
        latitude, longitude = cls.from_min_degrees(
            veh_gps_lat_ddmmmmmm, veh_gps_lon_dddmmmmmm
        )
        return GPSData(
            latitude=latitude,
            longitude=longitude,
            speed=veh_gps_vel_mpsd5 / 5,
            heading=veh_gps_hdg_deg5 * 2,
        )

    @classmethod
    def from_gtfs_vehicle(cls, gtfs_vehicle: Dict[str, Any]) -> "GPSData":
        return cls(
            latitude=gtfs_vehicle.get("latitude"),
            longitude=gtfs_vehicle.get("longitude"),
            speed=gtfs_vehicle.get("speed"),
            heading=gtfs_vehicle.get("bearing"),
        )
