from pyspark.sql.functions import acos, sin, cos, lit, toRadians
import xml.etree.ElementTree as ET


def haversine(lat_p1, lon_p1, lat_p2, lon_p2):
    # Returns the Great Circle Distance in m
    return (
        acos(
            sin(toRadians(lat_p1)) * sin(toRadians(lat_p2))
            + cos(toRadians(lat_p1))
            * cos(toRadians(lat_p2))
            * cos(toRadians(lon_p1) - toRadians(lon_p2))
        )
        * lit(6371.0)
        * lit(1000)
    )


# Find latitude and longitude from device config table (need to pass DeviceConfigurationXml as the parameter)
def findLatitude(xml):
    try:
        val = int(
            ET.fromstring(xml)
            .find("DeviceIdentity")
            .find("DeviceLocation")
            .find("LatitudeRaw")
            .text
        )
        if val < 0:
            val = val * (-1)
            coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
            coord = coord * (-1)
        else:
            coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
        return coord
    except:
        return 0.0


def findLongitude(xml):
    try:
        val = int(
            ET.fromstring(xml)
            .find("DeviceIdentity")
            .find("DeviceLocation")
            .find("LongitudeRaw")
            .text
        )
        if val < 0:
            val = val * (-1)
            coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
            coord = coord * (-1)
        else:
            coord = int(val / 1000000) + ((val / 10000) % 100 / 60)
        return coord
    except:
        return 0.0
