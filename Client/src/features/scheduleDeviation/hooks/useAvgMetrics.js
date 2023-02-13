import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useGetRoutesTableQuery } from '../api';
import openNotification from '../../../common/components/notification';
import { capitalize1stLetter } from '../../../common/utils';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../featurePersistence/store/selectors';

const useAvgMetrics = ({ routeName }) => {
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const onTimeRange = useSelector(selectTimeRange);

  const timeperiod = useSelector(selectTimeperiod);
  const { data: table, isFetching: isTableLoading } = useGetRoutesTableQuery({
    dateRange,
    direction,
    periods,
    onTimeRange,
    timeperiod,
  });

  const route = useMemo(() => {
    if (!table?.length) return null;
    return table.find(
      ({ route: tableRouteName }) => tableRouteName === routeName
    );
  }, [routeName, table]);

  const avgMetrics = useMemo(() => {
    if (!route) {
      return {};
    }

    const {
      avgScheduleDeviation,
      earlyPercentage,
      latePercentage,
      onTimePercentage,
    } = route;

    return {
      onTimePercentage: {
        onTimeRate: onTimePercentage,
        earlyRate: earlyPercentage,
        lateRate: latePercentage,
      },
      scheduleDeviation: {
        mins: avgScheduleDeviation,
      },
    };
  }, [route]);

  return {
    route,
    avgMetrics,
    isLoading: isTableLoading,
  };
};

export default useAvgMetrics;
