import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { convertRelativeToPercentages } from '../../../common/utils';
import { useGetAvgMetricsStopQuery, useGetLatenessPointsQuery } from '../api';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../featurePersistence/store/selectors';
/**
 * Check implementation compared to route-level stop metrics before use
 * @deprecated
 */
const useStop = ({ routeName, stopName }) => {
  const onTimeRange = useSelector(selectTimeRange);
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const timeperiod = useSelector(selectTimeperiod);

  const { data: stops, isFetching: isStopsLoading } = useGetLatenessPointsQuery(
    {
      routeName,
      dateRange,
      direction,
      periods,
      onTimeRange,
      timeperiod,
    }
  );
  const { data: metrics, isFetching: isMetricsLoading } =
    useGetAvgMetricsStopQuery();

  // Filter to selected stop
  const stop = useMemo(() => {
    const item = (stops || []).find(
      (point) => point.stopstartname === stopName
    );

    if (!item) return null;

    const [onTime, early, late] = convertRelativeToPercentages(
      [
        +item.ontimepercentage.percent,
        +item.earlypercentage.percent,
        +item.latepercentage.percent,
      ],
      1,
      (value) => value
    );

    return {
      ...item,
      lat: item.stopstartlatitude,
      lon: item.stopstartlongitude,
      lateness: item.stopstartlateness.mins,
      onTimePercentage: onTime,
      earlyPercentage: early,
      latePercentage: late,
      stopname: item.stopstartname,
      route: routeName,
    };
  }, [stops, routeName, stopName]);

  const avgMetrics = useMemo(() => {
    if (!metrics || !stop?.latenessreduction) return {};

    const { latenessreduction: stopScheduleDeviationMetrics } = stop;
    const { change, isBetter, mins } = stopScheduleDeviationMetrics;

    return {
      onTimePercentage: metrics?.onTimePercentage,
      scheduleDeviation: { change, isBetter, mins },
    };
  }, [stop, metrics]);

  const isLoading = useMemo(
    () => isMetricsLoading || isStopsLoading,
    [isMetricsLoading, isStopsLoading]
  );

  return {
    stop,
    avgMetrics,
    isLoading,
  };
};

export default useStop;
