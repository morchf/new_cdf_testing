import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useGetOverviewQuery } from '../api';
import {selectTimeperiod} from '../../featurePersistence/store/selectors';

const NUM_ROUTES_PER_DIRECTION = 3;

const useOverview = () => {
  const { direction, dateRange, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const timeperiod=useSelector(selectTimeperiod);
  const {data:routes, isFetching:isLoading}  = useGetOverviewQuery({
    dateRange,
    direction,
    periods,
    timeperiod,
    });

  const table = useMemo(() => {
    if (!routes) return null;

    const inMinutes = routes.map(
      ({ drivetime, dwelltime, signaldelay, traveltime, ...rest }) => ({
        drivetime: +drivetime / 60,
        dwelltime: +dwelltime / 60,
        signaldelay: +signaldelay / 60,
        traveltime: +traveltime / 60,
        ...rest,
      })
    );

    // Add metric for signal delay(in min) as percent of total travel time(in min)
    const wDelayAsPctTravel = inMinutes.map(
      ({ signaldelay, traveltime, ...rest }) => ({
        delayAsPctTravel: +signaldelay / +traveltime,
        signaldelay,
        traveltime,
        ...rest,
      })
    );

    return wDelayAsPctTravel;
  }, [routes]);

  // Extract performance
  const performance = useMemo(() => {
    if (!table?.length) return {};

    const sortedRoutes = table
      .slice()
      .filter(
        ({ signaldelay }) => signaldelay != null && !Number.isNaN(+signaldelay)
      )
      .sort(({ signaldelay: sd1 }, { signaldelay: sd2 }) => +sd1 - +sd2);
    const topRoutes = sortedRoutes.filter(
      (_, index) => index < NUM_ROUTES_PER_DIRECTION
    );
    const topUpdDate = topRoutes[topRoutes.length - 1].last_updated;

    const worstRoutes = sortedRoutes
      .reverse()
      .filter((_, index) => index < NUM_ROUTES_PER_DIRECTION);
    const worstUpdDate = worstRoutes[worstRoutes.length - 1].last_updated;

    return { topRoutes, topUpdDate, worstRoutes, worstUpdDate };
  }, [table]);

  return { performance, table,isLoading };
};

export default useOverview;
