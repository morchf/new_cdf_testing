const OFFSET_PERCENT = 0.15;

export const isInBounds = (bounds, { lat, lon }) => {
  if (!bounds) return true;

  const widthOffset = Math.abs(
    (bounds.ne.lon - bounds.sw.lon) * (OFFSET_PERCENT / 4)
  );
  const heightOffset = Math.abs(
    (bounds.ne.lat - bounds.sw.lat) * OFFSET_PERCENT
  );

  return (
    +lon < bounds.ne.lon + Math.sign(bounds.ne.lon) * widthOffset &&
    +lon > bounds.sw.lon - Math.sign(bounds.sw.lon) * widthOffset &&
    +lat < bounds.ne.lat - Math.sign(bounds.ne.lat) * heightOffset &&
    +lat > bounds.sw.lat + Math.sign(bounds.sw.lat) * heightOffset
  );
};

/**
 * Calculate squared Euclidean distance between two lat/long points
 * @param {object} point1
 * @param {number} point1.lat Latitude of point 1
 * @param {number} point1.lon Longitude of point 1
 * @param {object} point2
 * @param {number} point2.lat Latitude of point 2
 * @param {number} point2.lon Longitude of point 2
 * @return {number} Squared Euclidean distance
 */
export const squaredEuclideanDistance = (
  { lat: lat1, lon: lon1 },
  { lat: lat2, lon: lon2 }
) => (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2;

/**
 * Calculate the center of a bounds using Euclidean distance
 * @param {object} bounds
 * @param {object} bounds.ne NE lat/lonr pair
 * @param {object} bounds.sw SW lat/lonr pair
 * @return {object} center Center of the bounds as a lat/long pair
 * @return {number} center.lat Latitude
 * @return {number} center.lon Latitude
 */
export const boundsCenter = (bounds) => {
  if (
    !(bounds?.ne?.lat && bounds?.ne.lon && bounds?.sw?.lat && bounds?.sw.lon)
  ) {
    return { lat: 0, lon: 0 };
  }

  return {
    lat: (bounds.ne.lat + bounds.sw.lat) / 2,
    lon: (bounds.ne.lon + bounds.sw.lon) / 2,
  };
};

export const isWithinDistance = (l1, l2, distance) =>
  squaredEuclideanDistance(l1, l2) ** 0.5 < distance;
