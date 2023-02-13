import math
from typing import Dict, Optional

from geographiclib.geodesic import Geodesic


def merge(d: Dict, e: Dict, overwrite: Optional[bool] = False) -> Dict:
    """Merge two dictionaries, combining existing iterable and dictionary fields

    Args:
        d (Dict): Original dictionary
        e (Dict): Additional entries
        overwrite (Optional[bool]) Overwrite existing keys instead of combining

    Returns:
        Dict: Updated dictionary
    """
    for k, v in e.items():
        if k not in d.keys() or (overwrite and v is not None):
            d.update({k: v})
            continue

        # Merge repeat key-value pairs
        if isinstance(v, dict) and isinstance(d[k], dict):
            d.update({k: {**d[k], **v}})
            continue
        if isinstance(v, tuple) and isinstance(d[k], tuple):
            d.update(
                {
                    k: (*d[k], *v),
                }
            )
            continue
        if isinstance(v, list) and isinstance(d[k], list):
            d.update(
                {
                    k: [*d[k], *v],
                }
            )
            continue

        # Default to overwrite, if value is available
        if v is not None:
            d.update({k: v})

    return d


def chunk(arr, n):
    """
    Group array into chunks

    Args:
        l: Array
        n: Max size of each chunk

    Returns: Iterator with each batch
    """
    for i in range(0, len(arr), n):
        yield arr[i : (i + n)]  # noqa: E203


def coordinate_to_min_degrees(latlon):
    data = float(latlon)
    ddd = int(data)
    mmmmmm = float(data - float(ddd)) * 60
    data = (ddd * 1000000 + int(mmmmmm * 10000)) / 1000000
    return int(data * 1000000)


def coordinates_to_offset(lat, lon, offset_lat, offset_lon):
    g = Geodesic.WGS84.Inverse(lat, lon, offset_lat, offset_lon)

    distance, azimuth = [g[k] for k in ["s12", "azi2"]]  # azi2
    if azimuth > 0:
        azimuth -= 360
    azimuth = abs(azimuth)
    azimuth += 90
    azimuth %= 360
    rad = (azimuth / 180.0) * math.pi

    x = math.cos(rad) * distance
    y = math.sin(rad) * distance

    return x, y


def offset_to_coordinates(lat, lon, x, y):
    # calculate the angle in radians. This gives an angle in the range of 0 to 90 degrees based on which quadrant the x and y is present.
    if x == 0:
        rad = math.copysign(1, y) * math.pi / 2
    else:
        rad = math.atan(y / x)
    # convert 0 to 90 degrees to a 0 to 360 degree angle based on the quadrant.
    degrees = (rad * 180.0) / math.pi
    if (x < 0) & (y >= 0):
        degrees += 180
    elif (x < 0) & (y <= 0):
        degrees += 180
    elif (x >= 0) & (y <= 0):
        degrees += 360
    # convert it to a clockwise direction
    degrees = 360 - degrees
    # azimuth degree follows north as 0 degrees, east as 90 degrees, south as 180 degrees and west as 270 degrees
    # so there is an offset of 90 degrees when the angle is calculated in the clockwise direction.
    degrees += 90
    # making sure the degrees do not exceed 360.
    degrees %= 360
    # calculate distane in meters
    distance = math.sqrt(x**2 + y**2)

    # distance should in meters
    g = Geodesic.WGS84.Direct(lat, lon, degrees, distance)

    offset_lat, offset_lon = [g[k] for k in ["lat2", "lon2"]]  # azi2

    if x < 0 and (lat == 0 or (math.copysign(1, lat) != math.copysign(1, offset_lat))):
        offset_lat *= -1
        offset_lon *= -1

    return offset_lat, offset_lon
