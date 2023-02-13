// eslint-disable-next-line import/prefer-default-export
export const TooltipText = {
  Heading: 'Provides an overview of delays for all routes',
  Most: 'Most delayed routes based on signal delay at GTT intersections and filters',
  Least:
    'Least delayed routes based on signal delay at GTT intersections and filters',
  SignalDelay:
    'Average trip time elapsed while stopped at GTT intersections on route. Includes all (enabled and disabled) channels',
  DwellTime: 'Total time elapsed between arriving and departing at a bus stop',
  DriveTime:
    'Time elapsed between two stops including signal delay at non-GTT intersections. Excludes time spent at stops, segments and GTT intersections. Red map segments indicate an increase in drive time compared to previous date range.',
  TravelTime:
    'Total time elapsed between the start and the end of the route including dwell time, drive time and signal delay',
};

// 5% threshold used for determining if a stop or intersection has too little data
export const LOW_CONFIDENCE_THRESHOLD = 0.05;
