import ReactDOM from 'react-dom';
import { Metric } from '../../enums';
import { createShortTimeLabel } from '../../utils';
import { getLatestMetric } from '../../utils/metrics';
import {
  getMarkerColor,
  getPathColor,
  STATIC_MARKER_COLOR,
  STATIC_PATH_COLOR,
} from '../../utils/shapeColors';
import Marker from '../Marker';

// Legend Marker Icons
export const lineChartPath =
  'M0.75 6.9375 L 18.75 -5.4375 L 36 6.9375 L 52.125 1.6875';
export const dottedLinePath = 'M0 5 H6 M12 5 H24 M32 5 H38';
export const squarePath = 'M20 10 h 20 l 0 -10 l -20 0';

export const createStopTick = (index, stroke) => ({
  type: 'dataMarker',
  position: [+index, 0],
  offsetY: 12.5,
  line: {
    length: 25,
    style: {
      stroke,
      lineWidth: 2,
    },
  },
  text: false,
  point: false,
});

export const createStopsLine = (stroke) => ({
  type: 'line',
  start: ['min', 0],
  end: ['max', 0],
  style: {
    stroke,
    lineWidth: 2,
  },
});

export const createSegment = (index, stroke) => ({
  type: 'line',
  start: [+index, 0],
  end: [+index + 1, 0],
  style: {
    stroke,
    lineWidth: 2,
  },
});

export const createMarker = ({ index, value, title, onClick, ...props }) => ({
  type: 'html',
  position: [index, 0],
  html: () => {
    const el = document.createElement('div');
    el.title = title;
    el.addEventListener('click', onClick);
    ReactDOM.render(<Marker label={value} {...props} />, el);
    return el;
  },
});

export const createMetricMarkers = ({ data, metric, ...rest }) => {
  const markers = [];
  data.forEach((item, index) => {
    const value = Math.round(getLatestMetric(item?.periods, metric).mins);

    if (metric === Metric.DwellTime) {
      const color = getMarkerColor(metric, item.periods);
      // Not determined by item metric
      const isStaticColor =
        color === STATIC_PATH_COLOR || color === STATIC_MARKER_COLOR;

      // Do not need to redraw
      if (isStaticColor) return;

      // Add label
      markers.push(
        createMarker({
          index,
          value: createShortTimeLabel(value),
          title: item.stopname,
          style: { color },
          ...rest,
        })
      );

      // Add tick
      markers.push(createStopTick(index, color));

      return;
    }

    if (metric === Metric.DriveTime) {
      // Skip last segment
      if (index === data?.length - 1) return;

      const color = getPathColor(metric, item.periods);
      // Not determined by item metric
      const isStaticColor =
        color === STATIC_PATH_COLOR || color === STATIC_MARKER_COLOR;

      // Add label
      markers.push(
        createMarker({
          index: index + 0.5,
          value: createShortTimeLabel(value),
          title: `${item.stopname} to ${item.stopendname}`,

          // Keep existing color
          style: {
            color: !isStaticColor && color,
          },
          ...rest,
        })
      );

      // Do not need to redraw
      if (isStaticColor) return;

      // Add segment and ticks
      markers.push(createSegment(index, color));
      markers.push(createStopTick(index, color));
      markers.push(createStopTick(index + 1, color));
    }
  });

  return markers;
};

export const transformLegendItems = (legendItems) =>
  legendItems.map(({ field, label, symbol, stroke, fill = '' }) => ({
    id: field,
    value: field,
    name: field,
    label,
    marker: {
      symbol: () => symbol,
      style: {
        stroke,
        fill,
        lineWidth: 2,
      },
      spacing: 48,
    },
  }));

/**
 * Create visual indication of missing sections on a graph
 * @param {any[]} data Array of datapoints with potentially empty values
 * @param {string} field Field used to determine data prevalence
 * @return Annotations
 */
export const createUnusedZones = (data, field) => {
  const emptyAnnotations = [];
  data.forEach((item, index) => {
    if (index === 0 || index === data.length - 1) return;
    if (!Number.isNaN(+item[field])) return;

    let startIndex = index;
    let endIndex = index + 1;

    if (!Number.isNaN(+data[index - 1][field])) {
      // Leftmost period in empty section
      startIndex -= 0.75;

      // Both left and right valid
      if (!Number.isNaN(+data[index + 1][field])) {
        endIndex = startIndex + 1.5;
      }
    } else if (!Number.isNaN(+data[index + 1][field])) {
      // Rightmost period in empty section
      endIndex = startIndex + 0.75;
    }

    emptyAnnotations.push({
      type: 'region',
      start: [startIndex, 'min'],
      end: [endIndex, 'max'],
    });
  });

  // Add annotation for start
  if (Number.isNaN(+data[0][field])) {
    emptyAnnotations.push({
      type: 'region',
      start: [-0.25, 'min'],
      end: [
        // Adjust for first empty
        data.length >= 2 && !Number.isNaN(+data[1][field]) ? 0.75 : 1,
        'max',
      ],
    });
  }

  // Add annotation for end
  if (Number.isNaN(+data[data.length - 1][field])) {
    emptyAnnotations.push({
      type: 'region',
      start: [
        // Adjust for last empty
        data.length >= 2 && !Number.isNaN(+data[data.length - 2][field])
          ? data.length - 1.75
          : data.length - 1,
        'min',
      ],
      end: [data.length - 0.5, 'max'],
    });
  }

  return emptyAnnotations;
};
