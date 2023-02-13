import Point from "ol/geom/Point";
import MultiLineString from "ol/geom/MultiLineString";
import Feature from "ol/Feature";

// Map - required const value
// export const OSM_CORRECTION_FACTOR = 20037508.34;
import { OSM_CORRECTION_FACTOR } from "../../../constants";
import { findAbsMax } from "../utils";
import { getBusStopStyle, getLatenessPointStyle, getRouteStyle } from "./style";

export const latLonToMercator = (
  latLon,
  toFloat = false,
  yScale = 1,
  yOffset = 0
) => {
  const parsedLat = toFloat ? parseFloat(latLon[0]) : latLon[0];
  const parsedLon = toFloat ? parseFloat(latLon[1]) : latLon[1];

  const x = (parsedLon * OSM_CORRECTION_FACTOR) / 180;
  let y =
    Math.log(Math.tan(((90 + parsedLat) * Math.PI) / 360)) / (Math.PI / 180);
  y = (y * OSM_CORRECTION_FACTOR * yScale) / 180 + yOffset;

  return [x, y];
};

const gtfsToMercator = (latLon, yScale = 0.775, yOffset = 9849395) =>
  latLonToMercator(latLon, false, yScale, yOffset);

const drawRoutes = (data, withStops) => {
  const getBusStops = (route) => {
    if (Array.isArray(route?.stops)) {
      const stops = [...route.stops];
      // The first and the last items
      // are handled by getStart() and getEnd()

      // eslint-disable-next-line no-unused-expressions
      stops.length && stops.shift();
      // eslint-disable-next-line no-unused-expressions
      stops.length && stops.pop();

      const style = getBusStopStyle();

      return stops.map((stop) => {
        const feature = new Feature({
          geometry: new Point(gtfsToMercator(stop.location)),
          name: "bus-stop",
          stopname: stop.label,
        });
        feature.setStyle(style);

        return feature;
      });
    }

    return [];
  };

  const getRoute = (route, style) => {
    const points = route.points.map((point) => gtfsToMercator(point));
    const routeFeature = new Feature({
      geometry: new MultiLineString([points]),
    });
    routeFeature.setStyle(style);

    return routeFeature;
  };

  const getStart = (route, style) => {
    const start = route.stops[0];

    const feature = new Feature({
      geometry: new Point(gtfsToMercator(start?.location)),
      name: "start",
      stopname: start.label,
    });
    feature.setStyle(style);

    return start ? feature : undefined;
  };

  const getEnd = (route, style) => {
    const end = route.stops[route.stops.length - 1];

    const feature = new Feature({
      geometry: new Point(gtfsToMercator(end?.location)),
      name: "end",
      stopname: end.label,
    });
    feature.setStyle(style);

    return end ? feature : undefined;
  };

  const getRouteFeatures = () =>
    !data
      ? []
      : data.reduce((accumulator, route) => {
          const {
            multiLineStringOutlineStyle,
            multiLineStringStyle,
            startStyle,
            endStyle,
          } = getRouteStyle(route.color);

          return [
            ...accumulator,
            getStart(route, startStyle),
            getEnd(route, endStyle),
            ...(withStops ? getBusStops(route) : []),
            getRoute(route, multiLineStringOutlineStyle),
            getRoute(route, multiLineStringStyle),
          ];
        }, []);

  const draw = () => {
    const features = getRouteFeatures();

    return features;
  };

  return draw();
};

const drawRouteLateness = (data) => {
  const getLatenessPoints = () => {
    if (data?.length) {
      const latenessValues = data.map((item) => item.lateness);
      const absMaxLateness = findAbsMax(latenessValues);

      return data.map((point) => {
        const { direction, lat, lateness, lon, route, stopname } = point;

        const style = getLatenessPointStyle(lateness, absMaxLateness);

        const feature = new Feature({
          geometry: new Point(latLonToMercator([lat, lon], true)),
          lateness,
          name: "lateness-point",
          route: `Route ${route}`,
          stopname,
          direction: direction[0].toUpperCase() + direction.substring(1),
        });
        feature.setStyle(style);

        return feature;
      });
    }

    return [];
  };

  const getRouteFeatures = () => (!data ? [] : getLatenessPoints());

  const draw = () => {
    const features = getRouteFeatures();

    return features;
  };

  return draw();
};

export { drawRoutes, drawRouteLateness };
