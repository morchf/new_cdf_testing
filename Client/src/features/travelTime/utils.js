import { Metric } from '../../common/enums';

const mergeSegmentsWithMetrics = (segmentMetricsResponse) =>
  Array.isArray(segmentMetricsResponse)
    ? segmentMetricsResponse.reduce(
        (acc, item) => ({
          ...acc,
          [`${item.stopstart_id}-${item.stopend_id}`]: {
            numTrips: item.num_trips,
            stopname: item.stopstartname,
            stopendname: item.stopendname,
            stopstartid: item.stopstart_id,
            stopendid: item.stopend_id,
            lat: item.stopstartlatitude,
            lon: item.stopstartlongitude,
            periods: {
              ...acc[`${item.stopstart_id}-${item.stopend_id}`]?.periods,
              [item.period]: {
                drivetime: item.drivetime,
                dwelltime: item.dwelltime,
                traveltime: item.traveltime,
                signaldelay: item.signaldelay,
              },
            },
          },
        }),
        {}
      )
    : [];

/**
 * Combine datapoints from each intersection period to a per-intersection
 * datapoint with each point of data in a 'periods' field
 */
const mergeIntersectionsWithMetrics = (intersectionMetrics) =>
  Array.isArray(intersectionMetrics)
    ? Object.values(
        intersectionMetrics.reduce(
          (acc, item) => ({
            ...acc,
            [item.locationid]: {
              numTrips: item.num_trips,
              locationName: item.locationname,
              locationId: item.locationid,
              periods: {
                ...acc[item.locationid]?.periods,
                [item.period]: {
                  [Metric.SignalDelay]: {
                    ...item.signaldelay,
                    mins: item.signaldelay?.secs
                      ? item.signaldelay.secs / 60
                      : null,
                  },
                },
              },
            },
          }),
          {}
        )
      )
    : [];

export const inferStopOrder = (segments) =>
  segments?.length
    ? segments.map(({ ...rest }, index) => ({
        ...rest,
        stopstartorder: index + 1,
        stopendorder: index + 2,
      }))
    : [];

export { mergeSegmentsWithMetrics, mergeIntersectionsWithMetrics };
