import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useGetRouteSegmentsQuery } from '../api';
import { selectSelectedRoute, selectSelectedRoutes } from '../store/selectors';
import { setSelectedRoutes } from '../store/slice';

const useRoutes = ({ routeName }) => {
  const { direction, dateRange } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const { data: segments, isFetching: isLoading } = useGetRouteSegmentsQuery({
    routeName,
    direction,
    dateRange,
  });

  // Pull in selected routes
  const selectedRoutes = useSelector(selectSelectedRoutes);
  const selectedRoute = useSelector(selectSelectedRoute);

  // Update selected routes on fetch
  const dispatch = useDispatch();
  useEffect(() => {
    const route = segments?.filter(
      (routeItem) => routeItem.route === routeName
    )[0];
    dispatch(setSelectedRoutes(route ? [route] : []));
  }, [segments, routeName, dispatch]);

  return {
    routes: segments,
    isLoading,
    selectedRoutes,
    selectedRoute,
  };
};

export default useRoutes;
