import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useGetLatenessRoutesQuery } from '../api';
import { selectSelectedRoute, selectSelectedRoutes } from '../store/selectors';
import { setSelectedRoutes } from '../store/slice';

const useRoutes = ({ routeName }) => {
  const { dateRange, direction } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const { data: segments, isFetching: isLoading } = useGetLatenessRoutesQuery({
    routeName,
    dateRange,
    direction,
  });

  // Pull in selected routes
  const selectedRoutes = useSelector(selectSelectedRoutes);
  const selectedRoute = useSelector(selectSelectedRoute);

  // Update selected routes on fetch
  const dispatch = useDispatch();
  useEffect(() => {
    const selectedSegments = (segments || []).filter(
      (segment) => segment.route === routeName
    );
    dispatch(setSelectedRoutes(selectedSegments));
  }, [segments, routeName, dispatch]);

  return {
    routes: segments,
    isLoading,
    selectedRoute,
    selectedRoutes,
  };
};

export default useRoutes;
