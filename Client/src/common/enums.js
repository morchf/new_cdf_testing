export const Timeframe = {
  PeakAM: 'peak_am',
  PeakPM: 'peak_pm',
  OffPeak: 'offpeak',
  Weekends: 'weekend',
  All: 'all',
};

export const Direction = {
  Inbound: 'inbound',
  Outbound: 'outbound',
  All: 'all',
};

export const Period = {
  Day: 'day',
  Week: 'week',
  Month: 'month',
  Year: 'year',
};

export const Compare = {
  Previous: 'previous',
};

export const SortBy = {
  MostRecent: 'most-recent',
  Earliest: 'earliest',
};

export const PEAKS_DEFIINITION = [
  {
    end_time: '09:00:00',
    label: 'peak_am',
    start_time: '06:00:00',
  },
  {
    end_time: '19:00:00',
    label: 'peak_pm',
    start_time: '16:00:00',
  },
];

export const Metric = {
  ScheduleDeviation: 'scheduleDeviation',
  OnTimePercentage: 'onTimePercentage',
  SignalDelay: 'signaldelay',
  TravelTime: 'traveltime',
  DwellTime: 'dwelltime',
  DriveTime: 'drivetime',
};

export const Make = {
  GTT: 'GTT',
  SierraWireless: 'Sierra Wireless',
  Cradlepoint: 'Cradlepoint',
  Whelen: 'Whelen',
};

export const Model = {
  Model2101: '2101',
  MP70: 'MP-70',
  VSG: 'VSG',
  IBR900: 'IBR-900',
  IBR1700: 'IBR1700',
  R1900: 'R1900',
  Whelencom: 'Whelencom',
  WhelenDevice: 'WhelenDevice',
};
