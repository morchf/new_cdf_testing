import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { Period } from '../../../common/enums';
import { fillEmptyDates } from '../../../common/utils/dateRange';
import { useGetChartMetricsQuery } from '../api';
import { selectTimeperiod } from '../../featurePersistence/store/selectors';

const useMetricChart = ({ routeName, metric }) => {
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const { startDate, endDate } = dateRange;
  const timeperiod=useSelector(selectTimeperiod);
  const { data: charts, isFetching: isLoading } = useGetChartMetricsQuery({
    routeName,
    dateRange,
    direction,
    periods,
    period: 'day',
    timeperiod,
  });

  const chart = useMemo(
    () =>
      !charts?.length
        ? charts
        : fillEmptyDates({
            array: charts
              .map((item) => {
                if (item[metric]?.secs == null) {
                  return null;
                }

                return {
                  period: item.period,
                  value: parseFloat(item[metric]?.secs / 60) || 0,
                };
              })
              // Remove missing values
              .filter((item) => item != null),

            period: Period.Day,
            startDate,
            endDate,
          }),
    [charts, metric, startDate, endDate]
  );

  return { charts, chart, isLoading };
};

export default useMetricChart;
