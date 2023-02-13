import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useGetLatenessPerRouteTimeframeQuery } from '../api';
import { convertRelativeToPercentages } from '../../../common/utils';
import { fillEmptyDates } from '../../../common/utils/dateRange';
import { Period } from '../../../common/enums';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../featurePersistence/store/selectors';

const useTimeframe = ({ routeName }) => {
  const onTimeRange = useSelector(selectTimeRange);
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const { startDate, endDate } = dateRange;
  const timeperiod = useSelector(selectTimeperiod);

  const { data, isFetching: isLoading } = useGetLatenessPerRouteTimeframeQuery({
    routeName,
    dateRange,
    direction,
    periods,
    period: 'day',
    onTimeRange,
    timeperiod,
  });

  const timeframe = useMemo(() => {
    if (!data?.length) return data;

    // Map percents to equal 100%
    const mapped = data.map(
      ({ onTimePercentage, latePercentage, earlyPercentage, ...rest }) => {
        const [onTime, early, late] = convertRelativeToPercentages(
          [+onTimePercentage, +earlyPercentage, +latePercentage],
          1,
          (value) => value
        );

        return {
          ...rest,
          onTimePercentage: onTime,
          earlyPercentage: early,
          latePercentage: late,
        };
      }
    );

    return fillEmptyDates({
      array: mapped,
      period: Period.Day,
      startDate,
      endDate,
    });
  }, [data, startDate, endDate]);

  return {
    timeframe,
    isLoading,
  };
};

export default useTimeframe;
