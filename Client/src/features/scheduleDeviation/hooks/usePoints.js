import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { convertRelativeToPercentages } from '../../../common/utils';
import { useGetLatenessPointsQuery } from '../api';
import { Segment } from '../pages/routeDetails/shapes';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../featurePersistence/store/selectors';

const usePoints = ({ routeName }) => {
  const onTimeRange = useSelector(selectTimeRange);
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );

  const timeperiod = useSelector(selectTimeperiod);

  const { data, isFetching: isLoading } = useGetLatenessPointsQuery({
    routeName,
    dateRange,
    direction,
    periods,
    onTimeRange,
    timeperiod,
  });

  // Reduce raw response
  const reducedLatenessPoints = useMemo(() => {
    if (isLoading || !data) return [];

    const latestLatenessPoints = Object.values(
      (data || []).reduce(
        (acc, item) => ({
          ...acc,
          [Segment.getStopStartId(item)]: item,
        }),
        {}
      )
    );

    return latestLatenessPoints?.map((segment) => {
      const [onTime, early, late] = convertRelativeToPercentages(
        [
          +segment.ontimepercentage.percent,
          +segment.earlypercentage.percent,
          +segment.latepercentage.percent,
        ],
        1,
        (value) => value
      );

      return {
        ...segment,
        lat: segment.stopstartlatitude,
        lon: segment.stopstartlongitude,
        lateness: segment.stopstartlateness.mins,
        onTimePercentage: onTime,
        earlyPercentage: early,
        latePercentage: late,
        stopname: segment.stopstartname,
        route: routeName,
      };
    });
  }, [isLoading, data, routeName]);

  return { latenessPoints: reducedLatenessPoints, points: data, isLoading };
};

export default usePoints;
