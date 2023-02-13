import { Metric, Make, Model } from '../enums';

// Colors
export const PALETTE = {
  HIGHLIGHT1: '#FB8658',
  HIGHLIGHT2: '#7A1EC2',
  HIGHLIGHT3: '#211DE1',
  HIGHLIGHT4: '#3AB0D8',
};

export const COLOR_ERROR = '#aa3e19';
export const COLOR_WARNING = '#1765ad';
export const COLOR_NORMAL = '#8c8c8c';
export const COLOR_POSITIVE = '#1b722f';

export const COLOR_ON_TIME = '#D8D8D8';
export const COLOR_EARLY = '#F8E9B5';

export const metricColorMap = {
  [Metric.OnTimePercentage]: PALETTE.HIGHLIGHT1,
  [Metric.ScheduleDeviation]: PALETTE.HIGHLIGHT2,
  [Metric.SignalDelay]: PALETTE.HIGHLIGHT1,
  [Metric.TravelTime]: PALETTE.HIGHLIGHT2,
  [Metric.DwellTime]: PALETTE.HIGHLIGHT3,
  [Metric.DriveTime]: PALETTE.HIGHLIGHT4,
};

export const makeColorMap = {
  [Make.GTT]: 'green',
  [Make.SierraWireless]: 'pink',
  [Make.Cradlepoint]: 'purple',
  [Make.Whelen]: 'orange',
};

export const modelColorMap = {
  [Model.Model2101]: 'lightgrey',
  [Model.MP70]: 'lightgrey',
  [Model.VSG]: 'lightgrey',
  [Model.IBR900]: 'lightgrey',
  [Model.Whelencom]: 'orange',
  [Model.WhelenDevice]: 'orange',
};
