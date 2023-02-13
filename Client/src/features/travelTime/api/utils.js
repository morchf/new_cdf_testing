/* eslint-disable import/prefer-default-export */

/**
 * Add a minutes field to each metric
 * @param {[]} metrics
 * @param {number} secondsField Field with time data
 * @return {[]} Mapped metrics with `mins` field
 */
export const addMinutesToMetrics = (metrics, secondsField = 'secs') => {
  if (!metrics?.length) return metrics;
  return metrics.map(
    ({
      drivetime,
      dwelltime,
      signaldelay,
      traveltime,
      tspsavings,
      ...rest
    }) => ({
      ...rest,
      drivetime: {
        ...drivetime,
        mins: drivetime[secondsField] / 60,
      },
      dwelltime: {
        ...dwelltime,
        mins: dwelltime[secondsField] / 60,
      },
      signaldelay: {
        ...signaldelay,
        mins: signaldelay[secondsField] / 60,
      },
      traveltime: {
        ...traveltime,
        mins: traveltime[secondsField] / 60,
      },
      tspsavings: {
        ...tspsavings,
        mins: tspsavings[secondsField] / 60,
      },
    })
  );
};
