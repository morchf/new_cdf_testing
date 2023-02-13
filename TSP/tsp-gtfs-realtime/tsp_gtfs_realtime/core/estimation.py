import logging
import math
from abc import ABC, abstractmethod
from datetime import datetime

from gtt.data_model.rt_radio_message import GPSData


class PositionEstimationBase(ABC):
    @abstractmethod
    def update(self, gps_data: GPSData, time: datetime):
        pass

    @property
    def estimated_gps_data(self):
        """
        Returns:
            (float, float): Latitude and Longitude of current predicted position
        """
        return self.estimated_gps_data_at_time(datetime.now())

    @abstractmethod
    def estimated_gps_data_at_time(self, time: datetime):
        """
        Args:
            time (datetime): time at which to get predicted position

        Returns:
            (float, float): Latitude and Longitude of predicted position
        """
        pass


class SimplePositionEstimator(PositionEstimationBase):
    def __init__(self):
        self._last_updated = None
        self._latitude = None
        self._longitude = None
        self._speed = None
        self._heading = None

    def update(self, gps_data: GPSData, time: datetime = None):
        """update estimator with latest data

        Args:
            gps_data (GPSData):
              - latitude in degrees
              - longitude in degrees
              - speed in m/s
              - heading in degrees
            time (datetime, optional): timestamp of latest data, default: datetime.now()
        """
        if not (gps_data.latitude and gps_data.longitude):
            logging.warning(f"attempted to update position without data: {gps_data=}")
            return
        self._last_updated = time or datetime.now()
        self._latitude = gps_data.latitude
        self._longitude = gps_data.longitude
        self._speed = gps_data.speed
        self._heading = gps_data.heading

    def estimated_gps_data_at_time(self, time: datetime):
        """Simple extrapolation/dead reckoning for position estimation

        Args:
            time (datetime): time at which to get predicted position

        Returns:
            gps_data (GPSData): gps_data with predicted position if valid data, else None
        """
        # if never been updated with good data, just return None
        if not self._last_updated:
            return None

        # approximate distance conversion coefficients lat/lon using spherical earth
        # https://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
        # 111111 = 1e7 / 90
        latitude_m_per_deg = 111111
        longitude_m_per_deg = 111111 * math.cos(math.radians(self._latitude))

        # speed in m/s
        distance_m = (self._speed) * (time - self._last_updated).total_seconds()
        latitude_distance_m = distance_m * math.cos(math.radians(self._heading))
        longitude_distance_m = distance_m * math.sin(math.radians(self._heading))

        gps_data = None
        try:
            gps_data = GPSData(
                latitude=self._latitude + latitude_distance_m / latitude_m_per_deg,
                longitude=self._longitude + longitude_distance_m / longitude_m_per_deg,
                speed=self._speed,
                heading=self._heading,
            )
        except ValueError as validation_error:
            logging.error(
                f"Unable to set GPSData from {self.__class__}: {validation_error}"
            )

        return gps_data
