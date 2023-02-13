import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useGetAvgMetricsQuery } from '../api';
import { selectTimeperiod } from '../../featurePersistence/store/selectors';

const useStats = ({ routeName }) => {
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const timeperiod=useSelector(selectTimeperiod);
  const { data, isFetching: isLoading } = useGetAvgMetricsQuery({
    routeName,
    dateRange,
    direction,
    periods,
    timeperiod,
  });

  const latestMetrics = useMemo(() => (data?.length ? data[0] : data), [data]);

  return {
    avgMetrics: latestMetrics,
    isLoading,
  };
};

export default useStats;
