import {
  getPolyline,
  getMarker,
} from '../../../../common/components/Map/GMaps/drawShapes';
import { findAbsMax } from '../../../../common/components/Map/utils';
import { Metric } from '../../../../common/enums';
import BusStopSVG from '../../../../common/icons/BusStop.svg';
import { mapByGroup, take } from '../../../../common/utils/array';
import {
  boundsCenter,
  isInBounds,
  squaredEuclideanDistance,
} from '../../../../common/utils/map';
import { createTooltip } from '../../../../common/utils/shapes';

const MAX_NUM_TOOLTIPS = 5;

const getMarkerStyle = (latenessPoints, radiusField) => (marker) => {
  const latenessPointValues = Object.values(latenessPoints || {});

  const isNotEmpty = latenessPointValues.length;
  const stopValues = latenessPointValues?.map((item) => item[radiusField]);
  const maxAbsValue = isNotEmpty ? findAbsMax(stopValues) : 1;

  let radius = 0.8;
  let isOverZero = false;

  if (isNotEmpty) {
    const minRadius = 0.5;
    const maxRadius = 1.5;

    const relSize = Math.abs(marker[radiusField] / maxAbsValue);
    radius = minRadius + relSize * (maxRadius - minRadius);
    isOverZero = marker[radiusField] > 0;
  }

  return {
    path: 'M1-6c-3.866 0-7 3.133-7 7c0 3.865 3.134 7 7 7s7-3.135 7-7C8-2.867 4.866-6 1-6z',
    fillColor: isOverZero ? '#CB3541' : '#339933',
    fillOpacity: 1,
    strokeColor: '#E8E8E8',
    strokeWeight: 1,
    scale: radius,
    origin: 0,
  };
};

export const getPaths = (selectedRoute, strokeColor = '#676767') =>
  (selectedRoute?.segments || [])?.map((segment, i) =>
    getPolyline(
      segment,
      {
        strokeColor,
        strokeOpacity: 1,
        strokeWeight: 4,
      },
      `segment-${selectedRoute?.route}-${i}`
    )
  );

const metricImportance = (item, metric) => {
  if (metric === Metric.ScheduleDeviation) return Math.abs(+item.lateness);
  if (metric === Metric.OnTimePercentage) {
    return Number.isNaN(item.onTimePercentage)
      ? -1
      : 1 / +item.onTimePercentage;
  }
  return 0;
};

const metricValue = (item, metric) => {
  if (metric === Metric.ScheduleDeviation && !Number.isNaN(+item.lateness)) {
    const maxSeconds = 99;
    const minutes = item.lateness;
    const seconds = Math.round(+minutes * 60);
    const label = parseFloat(minutes) >= 0 ? 'ahead' : 'behind';
    const units = seconds >= 60 ? 'min' : 'sec';

    if (seconds <= maxSeconds) {
      const value = seconds < 0 ? Math.abs(seconds) : seconds;
      return `${value}\n${units}\n${label}`;
    }

    const value = seconds >= 60 ? Math.round(+minutes) : seconds;

    return `${value}\n${units}\n${label}`;
  }

  if (
    metric === Metric.OnTimePercentage &&
    !Number.isNaN(item.onTimePercentage)
  )
    return `${+item.onTimePercentage.toFixed(0)}\n%`;

  return '--\nNo Data';
};

export const createPoints = ({ stops, onClick, bounds, metric }) => {
  const center = boundsCenter(bounds);
  const boundsDistance = bounds
    ? Math.abs(bounds.ne.lat - bounds.sw.lat) * 0.05
    : 0;

  const icons = stops.map((stop, i) =>
    getMarker(
      stop,
      onClick,
      {
        url: BusStopSVG,
        // Half th height/width of the BusStopSVG
        anchor: { x: 10, y: 10 },
      },
      `stop-${stop.direction}-${stop.lat}-${stop.lon}`
    )
  );

  const validStops = stops
    // Make displayed tooltips tend toward center of screen
    .sort(
      (s1, s2) =>
        squaredEuclideanDistance(s1, center) -
        squaredEuclideanDistance(s2, center)
    )
    // Filter out points not shown and sort by worst metric
    .sort((s1, s2) => {
      if (!isInBounds(bounds, s1)) return 1;
      if (!isInBounds(bounds, s2)) return -1;

      return metricImportance(s2, metric) - metricImportance(s1, metric);
    });

  // Select tooltips that aren't too close
  const selectedStops = take(validStops, MAX_NUM_TOOLTIPS);

  const markers = selectedStops.map((stop) =>
    createTooltip({
      position: stop,
      onClick,
      text: metricValue(stop, metric),
      key: `stop-tooltip-${stop.direction}-${stop.lat}-${stop.lon}`,
      suffix: metric === Metric.ScheduleDeviation ? '--sd' : '',
    })
  );

  return [...icons, ...markers];
};

/**
 * Utility class for segment objects
 */
export class Segment {
  static createKey(...keys) {
    return (keys || []).filter((value) => !!value).join('-');
  }

  static getLocationIdStart(segment) {
    return `${segment.stopstartlat}-${segment.stopstartlon}-${segment.direction}`;
  }

  static getLocationIdEnd(segment) {
    return `${segment.stopendlat}-${segment.stopendlon}-${segment.direction}`;
  }

  static getStopStartId(segment) {
    const primaryKey = segment.stopstartname;
    const ordinalKey =
      'stopstartorder' in segment ? segment.stopstartorder : null;

    return Segment.createKey(primaryKey, segment.direction, ordinalKey);
  }

  static getStopEndId(segment) {
    const primaryKey = segment.stopendname;
    const ordinalKey = 'stopendorder' in segment ? segment.stopendorder : null;

    return Segment.createKey(primaryKey, segment.direction, ordinalKey);
  }
}

const extractUniqueStopsFromSegments = (segments) => {
  if (!segments?.length) return [];

  return Object.values(
    segments.reduce(
      (acc, item) => ({
        ...acc,
        [Segment.getLocationIdStart(item)]: {
          ...item,
          ...acc[Segment.getLocationIdStart(item)],
          stopname: item.stopstartname,
          stoporder: item.stopstartorder,
          stoplat: item.stopstartlat,
          stoplon: item.stopstartlon,
          direction: item.direction,
        },
        [Segment.getLocationIdEnd(item)]: {
          ...item,
          ...acc[Segment.getLocationIdEnd(item)],
          stopname: item.stopendname,
          stoporder: item.stopendorder,
          stoplat: item.stopendlat,
          stoplon: item.stopendlon,
          direction: item.direction,
        },
      }),
      {}
    )
  );
};

export const leftJoin = (sortedStops, mapPoints) => {
  const routeName = mapPoints ? mapPoints[0]?.route : null;
  const stopsWithMetrics = sortedStops
    .map((a) => ({
      ...mapPoints.find(
        (b) => a.direction === b.direction && a.stopname === b.stopname
      ),
      ...a,
    }))
    .map((val) => ({
      stopid: val.stopid,
      stoporder: val.stoporder,
      stopname: val.stopname,
      lat: val.stoplat,
      lon: val.stoplon,
      lateness: val.lateness,
      earlypercentage: val.earlypercentage,
      ontimepercentage: val.ontimepercentage,
      latepercentage: val.latepercentage,
      route: routeName,
      direction: val.direction,
    }));

  return stopsWithMetrics;
};

export const joinMetricsSegments = (segments, metricsPoints) => {
  const sortedStops = extractUniqueStopsFromSegments(segments).sort((a, b) => {
    if (a.direction !== b.direction) {
      return (a.direction || '').localeCompare(b.direction);
    }

    return +a.stoporder - +b.stoporder;
  });

  // Left join sortedStops with mapPoints by stopid
  const stopsWithMetrics = leftJoin(sortedStops, metricsPoints);

  return mapByGroup(stopsWithMetrics, 'direction', (item, index) =>
    item ? { ...item, stopNumber: index + 1 } : item
  );
};
