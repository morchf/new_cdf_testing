import { SEGMENT_MAP_METRICS, metricColorMap } from '../constants';
import { Metric } from '../enums';
import { getLatestMetric } from './metrics';

export const DEFAULT_COLOR = '#676767';
export const STATIC_MARKER_COLOR = '#339933';
export const STATIC_PATH_COLOR = '#3AB0D8';
export const WARNING_COLOR = '#CB3541';

export const getMarkerColor = (selectedMetric, markerPeriods) => {
  if (SEGMENT_MAP_METRICS.includes(selectedMetric)) {
    return DEFAULT_COLOR;
  }

  const metric = getLatestMetric(markerPeriods, selectedMetric);
  if (selectedMetric === Metric.DwellTime) {
    return STATIC_MARKER_COLOR;
  }

  if (metric?.isBetter != null) {
    return !metric.isBetter ? WARNING_COLOR : STATIC_MARKER_COLOR;
  }

  return STATIC_MARKER_COLOR;
};

export const getPathColor = (selectedMetric, segmentPeriod) => {
  if (selectedMetric !== Metric.DriveTime) {
    return metricColorMap[selectedMetric] || DEFAULT_COLOR;
  }

  const metric = getLatestMetric(segmentPeriod, selectedMetric);
  // Below used for coloring based on 'isBetter'
  if (metric?.isBetter != null) {
    return !metric.isBetter ? '#AD1515' : STATIC_PATH_COLOR;
  }

  return STATIC_PATH_COLOR;
};
