import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { convertRelativeToPercentages } from '../../../common/utils';
import { useGetRoutesTableQuery } from '../api';
import { DeviationCategory } from '../constants';
import { getDeviationCategory } from '../utils';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../featurePersistence/store/selectors';

const NUM_ROUTES_PER_DIRECTION = 2;

const useOverview = () => {
  const onTimeRange = useSelector(selectTimeRange);

  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const timeperiod = useSelector(selectTimeperiod);

  const { data: table, isFetching: isLoading } = useGetRoutesTableQuery({
    dateRange,
    direction,
    periods,
    onTimeRange,
    timeperiod,
  });

  const [onTimeLower, onTimeUpper] = [onTimeRange];

  const overview = useMemo(() => {
    if (!table?.length) return {};

    const sortedRoutes = table
      .slice()
      .filter(
        ({ onTimePercentage }) =>
          onTimePercentage != null && !Number.isNaN(+onTimePercentage)
      )
      .sort(
        ({ onTimePercentage: ot1 }, { onTimePercentage: ot2 }) => +ot1 - +ot2
      )
      .map(({ avgScheduleDeviation, ...rest }) => ({
        ...rest,
        avgScheduleDeviation,
        category: getDeviationCategory(
          avgScheduleDeviation,
          onTimeLower,
          onTimeUpper
        ),
      }));
    const worstRoutes = sortedRoutes.filter(
      (_, index) => index < NUM_ROUTES_PER_DIRECTION
    );

    const topRoutes = sortedRoutes
      .reverse()
      .filter((_, index) => index < NUM_ROUTES_PER_DIRECTION);

    const numOnTime = sortedRoutes.filter(
      ({ category }) => category === DeviationCategory.OnTime
    ).length;
    const numLate = sortedRoutes.filter(
      ({ category }) => category === DeviationCategory.Late
    ).length;
    const numEarly = sortedRoutes.filter(
      ({ category }) => category === DeviationCategory.Early
    ).length;

    const totalNum = table?.length;

    const [onTimePercentage, latePercentage, earlyPercentage] =
      convertRelativeToPercentages(
        [numOnTime / totalNum, numEarly / totalNum, numLate / totalNum],
        2,
        (value) => value
      );

    const overall = {
      onTime: {
        num: numOnTime,
        totalNum,
        percentage: onTimePercentage,
      },
      late: {
        num: numLate,
        totalNum,
        percentage: latePercentage,
      },
      early: {
        num: numEarly,
        totalNum,
        percentage: earlyPercentage,
      },
    };

    return {
      worst: {
        routes: worstRoutes,
      },
      top: {
        routes: topRoutes,
      },
      overall,
    };
  }, [onTimeLower, onTimeUpper, table]);

  return {
    overview,
    table,
    isLoading,
  };
};

export default useOverview;
