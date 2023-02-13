import {
  getPolyline,
  getMarker,
} from '../../../../common/components/Map/GMaps/drawShapes';
import { SEGMENT_MAP_METRICS } from '../../../../common/constants';
import BusStopSVG from '../../../../common/icons/BusStop.svg';
import BusStopLowConfidence from '../../../../common/icons/BusStopLowConfidence.svg';
import BusStopWarnSVG from '../../../../common/icons/BusStopWarn.svg';
import IntersectionSVG from '../../../../common/icons/Intersection.svg';
import IntersectionLowConfidenceSVG from '../../../../common/icons/IntersectionLowConfidence.svg';
import { Metric } from '../../../../common/enums';
import { getPathColor } from '../../../../common/utils/shapeColors';
import { getLatestMetric } from '../../../../common/utils/metrics';
import { createShortTimeLabel } from '../../../../common/utils';
import { isInBounds } from '../../../../common/utils/map';
import { createTooltip } from '../../../../common/utils/shapes';
import { take } from '../../../../common/utils/array';
import { LOW_CONFIDENCE_THRESHOLD } from '../../constants';

const linePath = 'M0 0, L0 12';

const NUM_ANGLES = 4;
const createLinePath = (angle) => {
  const snappedAngle =
    (Math.PI * 2 * Math.round((angle / (2 * Math.PI)) * NUM_ANGLES)) /
    NUM_ANGLES;

  const x = Math.cos(snappedAngle) * 6;
  const y = Math.sin(snappedAngle) * 6;
  return `M${-x} ${-y}, L${x} ${y}`;
};

const MAX_NUM_TOOLTIPS = 5;

const visibleMetricComparator =
  ({ metric, bounds }) =>
  (s1, s2) => {
    if (!isInBounds(bounds, s1)) return 1;
    if (!isInBounds(bounds, s2)) return -1;

    if (!s1?.periods) return 1;
    if (!s2?.periods) return -1;

    return (
      +getLatestMetric(s2.periods, metric)?.mins -
      +getLatestMetric(s1.periods, metric)?.mins
    );
  };

export const getPaths = (
  travelTimeMetrics = {},
  selectedMetric,
  selectedRoute,
  setSelectedMarker
) =>
  (selectedRoute?.segments || [])?.map((segment, i) => {
    const segmentData =
      travelTimeMetrics[`${segment.stopstartid}-${segment.stopendid}`];
    const strokeColor = getPathColor(selectedMetric, segmentData?.periods);

    const handleClick = (clickedSegment) => {
      if (setSelectedMarker) {
        const tooltipPoint =
          clickedSegment?.points[
            Math.floor(clickedSegment?.points?.length / 2)
          ];

        if (SEGMENT_MAP_METRICS.includes(selectedMetric)) {
          setSelectedMarker({
            lat: parseFloat(tooltipPoint.lat),
            lon: parseFloat(tooltipPoint.lon),
            periods: clickedSegment?.periods,
            stopname: clickedSegment?.name,
          });
        }
      }
    };

    return getPolyline(
      {
        ...segment,
        periods: segmentData?.periods,
        name: `Segment ${segment.stopstartname} - ${segment.stopendname}`,
      },
      {
        strokeOpacity: 1,
        strokeWeight: 4,
        strokeColor,
      },
      `segment-${selectedRoute?.route}-${segment.stopstartname}-${segment.stopendname}-${i}`,
      handleClick
    );
  });

export const leftJoin = (sortedStops, mapPoints) => {
  const stopsWithMetrics = sortedStops
    .map((a) => ({
      ...mapPoints.find((b) => a.stopid === b.stopendid),
      ...a,
    }))
    .map((val) => ({
      numTrips: val.numTrips,
      stopid: val.stopid,
      stoporder: val.stoporder,
      stopname: val.stopname,
      lat: val.stoplat,
      lon: val.stoplon,
      periods: val.periods,
    }));

  return stopsWithMetrics;
};

const createMetricTooltip = ({ minutes, maxSeconds, ...rest }) =>
  createTooltip({
    text: createShortTimeLabel(minutes, maxSeconds),
    ...rest,
  });

const createBusStopIcon = ({
  metric,
  marker,
  key,
  onClick,
  isSelected = false,
  numTrips,
  totalTrips,
}) => {
  const url =
    numTrips < totalTrips * LOW_CONFIDENCE_THRESHOLD &&
    metric !== Metric.DriveTime
      ? BusStopLowConfidence
      : BusStopSVG;

  const callback = onClick || (() => {});
  return getMarker(
    marker,
    callback,
    {
      url,
      // Half the height/width of the BusStopSVG
      anchor: { x: 10, y: 10 },
    },
    key
  );
};

export const createIntersectionIcon = ({
  marker,
  key,
  onClick,
  numTrips,
  totalTrips,
}) =>
  getMarker(
    marker,
    onClick,
    {
      url:
        numTrips < totalTrips * LOW_CONFIDENCE_THRESHOLD
          ? IntersectionLowConfidenceSVG
          : IntersectionSVG,
      // Half the height/width of the BusStopSVG
      anchor: { x: 11, y: 10 },
    },
    key
  );

export const createTravelTimeMarkers = ({ travelTime, stops }) => {
  const middlePoint = stops?.length
    ? stops[Math.round(stops.length / 2)]
    : null;

  if (!middlePoint) return [];

  return [
    createMetricTooltip({
      position: middlePoint,
      minutes: travelTime,
      placement: 'top',
      key: 'travel-time',
      maxSeconds: 59,
      onClick: () => {},
    }),
  ];
};

export const createPoints = ({
  metric,
  onClick = () => {},
  stops = [],
  intersections = [],
  bounds,
  totalTrips,
}) => {
  const markers = [];
  const icons = [];

  const boundsDistance = bounds
    ? Math.abs(bounds.ne.lat - bounds.sw.lat) * 0.05
    : 0;

  // Option to toggle marker direction
  const top = true;

  /* Stops */

  if (metric !== Metric.SignalDelay) {
    const sortedStops = (stops || []).sort(
      visibleMetricComparator({ metric, bounds })
    );

    // Select tooltips that aren't too close
    sortedStops.forEach((stop) => {
      stop.isSelected = false;
    });
    take(sortedStops, MAX_NUM_TOOLTIPS).forEach((stop) => {
      stop.isSelected = true;
    });

    sortedStops.forEach((stop, i) => {
      if (stop.periods === undefined) {
        // Empty stops
        icons.push(
          createBusStopIcon({
            marker: stop,
            key: `stop-${stop.lat}-${stop.lon}`,
            onClick: metric === Metric.DriveTime ? () => {} : onClick,
          })
        );
        return;
      }

      const minutes = +getLatestMetric(stop.periods, metric)?.mins;
      const isSelected = metric === Metric.DwellTime && stop.isSelected;

      // Bus stop icon
      icons.push(
        createBusStopIcon({
          metric,
          marker: stop,
          key: `stop-${stop.lat}-${stop.lon}`,
          onClick: metric === Metric.DriveTime ? () => {} : onClick,
          numTrips: stop.numTrips,
          totalTrips,
        })
      );

      // Tooltip
      if (
        metric === Metric.DwellTime &&
        (isSelected || Number.isNaN(minutes))
      ) {
        // Add tooltips
        markers.push(
          createMetricTooltip({
            position: stop,
            onClick,
            minutes,
            placement: top ? 'top' : 'bottom',
            key: `stop-tooltip-${stop.lat}-${stop.lon}`,
          })
        );
      }
    });

    return [...icons, ...markers];
  }

  /* Intersections */

  const sortedIntersections = (intersections || []).sort(
    visibleMetricComparator({ metric, bounds })
  );

  // Flag the selected intersections
  sortedIntersections.forEach((intersection) => {
    intersection.isSelected = false;
  });
  take(sortedIntersections, MAX_NUM_TOOLTIPS).forEach((intersection) => {
    intersection.isSelected = true;
  });

  sortedIntersections.forEach((intersection, i) => {
    const { lat, lon } = intersection;

    // Point
    const minutes = +getLatestMetric(intersection.periods, metric)?.mins;
    const { isSelected } = intersection;

    if (lat == null || lon == null) return;

    // Intersection icon
    icons.push(
      createIntersectionIcon({
        marker: intersection,
        key: `intersection-${lat}-${lon}`,
        onClick,
        numTrips: intersection.numTrips,
        totalTrips,
      })
    );

    // Tooltip
    if (isSelected) {
      markers.push(
        createMetricTooltip({
          position: intersection,
          onClick,
          minutes,
          placement: top ? 'top' : 'bottom',
          key: `intersection-tooltip-${lat}-${lon}`,
        })
      );
    }
  });

  return [...icons, ...markers];
};

export const joinMetricsIntersections = ({ locations, metrics }) =>
  metrics.map(({ periods, locationId, locationName, numTrips }) => {
    const { latitude: lat, longitude: lon } = locations[locationId] || {};
    return { periods, locationId, locationName, lat, lon, numTrips };
  });
