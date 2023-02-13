export const formatTimeframePoints = (points) =>
  points.map(
    ({
      eventdate,
      stopstartlateness,
      ontimepercentage,
      earlypercentage,
      latepercentage,
      ...rest
    }) => ({
      period: eventdate,
      lateness: stopstartlateness?.secs / 60,
      onTimePercentage: ontimepercentage.percent,
      earlyPercentage: earlypercentage.percent,
      latePercentage: latepercentage.percent,
      stopstartlateness,
      ...rest,
    })
  );

/**
 * Add a minutes field to each metric
 * @param {[]} metrics
 * @param {number} secondsField Field with time data
 * @return {[]} Mapped metrics with `mins` field
 */
export const addMinutesToMetrics = (metrics, secondsField = 'secs') => {
  if (!metrics?.length) return metrics;
  return metrics.map(
    ({ latenessreduction, stopstartlateness, stopendlateness, ...rest }) => ({
      ...rest,
      latenessreduction: {
        ...latenessreduction,
        mins: latenessreduction[secondsField] / 60,
      },
      stopstartlateness: {
        ...stopstartlateness,
        mins: stopstartlateness[secondsField] / 60,
      },
      stopendlateness: {
        ...stopendlateness,
        mins: stopendlateness[secondsField] / 60,
      },
    })
  );
};
