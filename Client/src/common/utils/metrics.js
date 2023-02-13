// eslint-disable-next-line import/prefer-default-export
export const getLatestMetric = (periods, metric) => {
  const periodsArray = Object.values(periods || {});
  if (!periodsArray.length) return {};
  return periodsArray[periodsArray.length - 1]?.[metric];
};
