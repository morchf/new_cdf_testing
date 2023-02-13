/**
 * Calculate the zoom level for the current map dimensions and bounds
 *
 * @see https://stackoverflow.com/questions/6048975/google-maps-v3-how-to-calculate-the-zoom-level-for-a-given-bounds
 * @param {google.maps.LatLngBounds} bounds Bounds to set viewport
 * @param {object} mapDim Dimensions of the map container
 * @param {number} mapDim.width
 * @param {number} mapDim.height
 * @return {number} Appropriate zoom level
 */
const getBoundsZoomLevel = (bounds, mapDim) => {
  const WORLD_DIM = { height: 256, width: 256 };
  const ZOOM_MAX = 21;

  function latRad(lat) {
    const sin = Math.sin((lat * Math.PI) / 180);
    const radX2 = Math.log((1 + sin) / (1 - sin)) / 2;
    return Math.max(Math.min(radX2, Math.PI), -Math.PI) / 2;
  }

  function zoom(mapPx, worldPx, fraction) {
    return Math.floor(Math.log(mapPx / worldPx / fraction) / Math.LN2);
  }

  const ne = bounds.getNorthEast();
  const sw = bounds.getSouthWest();

  const latFraction = (latRad(ne.lat()) - latRad(sw.lat())) / Math.PI;

  const lngDiff = ne.lng() - sw.lng();
  const lngFraction = (lngDiff < 0 ? lngDiff + 360 : lngDiff) / 360;

  const latZoom = zoom(mapDim.height, WORLD_DIM.height, latFraction);
  const lngZoom = zoom(mapDim.width, WORLD_DIM.width, lngFraction);

  return Math.min(latZoom, lngZoom, ZOOM_MAX);
};

export const fitGMap = (locations = [], mapRef, mapDim) => {
  if (!mapRef || !mapDim) return;

  const LatLngBounds = window?.google?.maps?.LatLngBounds;
  const LatLng = window?.google?.maps?.LatLng;

  const bounds = LatLngBounds ? new LatLngBounds() : null;

  if (!bounds || !Array.isArray(locations) || !window?.google) return;

  locations?.forEach(({ lat, lng }) => {
    const newLatLng = LatLng ? new LatLng(lat, lng) : null;

    if (bounds && newLatLng) {
      bounds.extend(newLatLng);
    }
  });

  // Appropriate zoom level with spacing
  const zoom = getBoundsZoomLevel(bounds, mapDim) - 0.25;

  // Use asynchronous listener to set zoom
  if (window?.google?.maps?.event) {
    window.google.maps.event.addListenerOnce(mapRef, 'bounds_changed', () => {
      mapRef.setZoom(zoom);
    });
  }

  mapRef.setCenter(bounds.getCenter());
  mapRef.fitBounds(bounds);
};
