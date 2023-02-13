import {
  Metric,
  Period,
  Timeframe,
  Direction,
  PEAKS_DEFIINITION,
} from '../enums';

// Label maps
export const metricsNames = {
  signaldelay: 'Signal Delay',
  dwelltime: 'Dwell Time',
  drivetime: 'Drive Time',
  traveltime: 'Travel Time',
  scheduleDeviation: 'Schedule Deviation',
  onTimePercentage: 'On-Time Percentage',
};

// Shapes
export const SEGMENT_MAP_METRICS = [Metric.DriveTime];

export const PERIODS = [
  {
    label: `Peak AM (06:00 - 09:00)`,
    value: Timeframe.PeakAM,
  },
  {
    label: `Peak PM (16:00 - 19:00)`,
    value: Timeframe.PeakPM,
  },
  {
    label: 'Off-Peak (not peak or weekends)',
    value: Timeframe.OffPeak,
  },
  {
    label: 'Weekends (Saturday & Sunday)',
    value: Timeframe.Weekends,
  },
  {
    label: 'All',
    value: Timeframe.All,
  },
];

export const DIRECTIONS = Object.values(Direction);

export const TIMEPERIODS = Object.values(Timeframe);

export const BREADCRUMB_TITLES = {
  analytics: {
    title: 'Analytics',
  },
  'schedule-deviation': {
    title: 'Schedule Deviation',
    to: '/analytics/schedule-deviation',
  },
  'transit-delay': {
    title: 'Transit Delay',
    to: '/analytics/transit-delay',
  },
  'health-monitoring': {
    title: 'Health Monitoring',
  },
  intersections: {
    title: 'Intersections',
    to: '/health-monitoring/intersections',
  },
  vehicles: {
    title: 'Vehicles',
    to: '/health-monitoring/vehicles',
  },
};

// Dates
export const PERIOD_FREQUENCY = {
  [Period.Day]: Period.Day,
  [Period.Week]: Period.Day,
  [Period.Month]: Period.Day,
  [Period.Year]: Period.Month,
};
