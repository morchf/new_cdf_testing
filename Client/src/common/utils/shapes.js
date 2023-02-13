import { getMarker } from '../components/Map/GMaps/drawShapes';
import FlagStartSVG from '../icons/FlagStart.svg';
import MarkerBottomSVG from '../icons/MarkerBottom.svg';
import MarkerTopSVG from '../icons/MarkerTop.svg';

// eslint-disable-next-line import/prefer-default-export
export const createFlags = ({ stops, direction }) => {
  if (!stops?.length) return [];

  const start = stops[0];

  // Can be used for flag at end
  // const end = stops[stops.length - 1];

  return [
    getMarker(
      start,
      () => {},
      {
        url: FlagStartSVG,
        anchor: { x: 0, y: 28 },
      },
      `flag-${direction}`
    ),
  ];
};

export const joinSignalDelayMetricsSegments = (segments, metrics, leftJoin) => {
  // filter unique stops from segments
  const stops = segments?.length
    ? segments.reduce(
        (acc, item) => ({
          ...acc,
          [item.stopstartid]: {
            ...acc[item.stopstartid],
            stopname: item.stopstartname,
            stopid: item.stopstartid,
            stoporder: item.stopstartorder,
            stoplat: item.stopstartlat,
            stoplon: item.stopstartlon,
          },
          [item.stopendid]: {
            ...acc[item.stopendid],
            stopname: item.stopendname,
            stopid: item.stopendid,
            stoporder: item.stopendorder,
            stoplat: item.stopendlat,
            stoplon: item.stopendlon,
          },
        }),
        []
      )
    : [];
  const filteredStops = Object.values(stops || {});
  const sortedStops = filteredStops?.length
    ? filteredStops.sort(
        (a, b) => parseInt(a.stoporder, 10) - parseInt(b.stoporder, 10)
      )
    : [];

  const mapPoints = Object.values(metrics || {})
    .sort((a, b) => a.stopendid - b.stopendid || b.stopstartid - a.stopstartid)
    .map((a) => ({
      ...sortedStops.find((b) => a.stopendid === b.stopid),
      ...a,
    }))
    .map((val) => ({
      numTrips: val.numTrips,
      stopendid: val.stopendid,
      stopendorder: val.stoporder,
      stopendname: val.stopendname,
      lat: val.lat,
      lon: val.lon,
      periods: val.periods,
      stopname: val.stopname,
      stopstartid: val.stopstartid,
    }))
    .map((a) => ({
      ...sortedStops.find((b) => a.stopstartid === b.stopid),
      ...a,
    }))
    .map((val) => ({
      numTrips: val.numTrips,
      stopendid: val.stopendid,
      stopendorder: val.stopendorder,
      stopstartid: val.stopstartid,
      stopstartorder: val.stoporder,
      stopendname: val.stopendname,
      periods: val.periods,
      stopname: val.stopname,
    }))
    .filter(
      (segment) =>
        parseInt(segment.stopendorder, 10) -
          parseInt(segment.stopstartorder, 10) >
        0
    ) // stopstartorder should be smaller than stopendorder
    .sort(
      (a, b) =>
        a.stopendorder - b.stopendorder || b.stopstartorder - a.stopstartorder
    ); // if multiple segments for a same stopend, sort from the closest stop;

  // Left join sortedStops with mapPoints by stopid
  const stopsWithMetrics = leftJoin(sortedStops, mapPoints);

  return stopsWithMetrics.map((item, index) =>
    item ? { ...item, stopNumber: index + 1 } : item
  );
};

export const createTooltip = ({
  position,
  text,
  onClick = () => {},
  placement = 'top',
  key = '',
  suffix = '',
}) => {
  if (!position) return null;

  return getMarker(
    position,
    onClick,
    {
      url: placement === 'top' ? MarkerTopSVG : MarkerBottomSVG,
      // Place the icon relative to the stop/intersection
      anchor: placement === 'top' ? { x: 8, y: 75 } : { x: 8, y: 15 },
    },
    `tooltip-${key}`,
    {
      text,
      className: `tooltip-map${suffix} ${
        placement === 'top' ? 'tooltip-map--top' : ''
      } ${!text || text.length === 1 ? 'tooltip-map--empty' : ''}`,
    }
  );
};
