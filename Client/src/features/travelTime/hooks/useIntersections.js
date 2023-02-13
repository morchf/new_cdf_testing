import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useGetIntersectionsQuery, useGetSignalDelayQuery } from '../api';
import { joinMetricsIntersections } from '../pages/routeDetails/shapes';
import { selectTimeperiod } from '../../featurePersistence/store/selectors';

const useIntersections = ({ routeName }) => {
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const timeperiod = useSelector(selectTimeperiod);
  const { data: signalDelay, isFetching: isSignalDelayLoading } =
    useGetSignalDelayQuery({
      routeName,
      dateRange,
      direction,
      periods,
      timeperiod,
    });

  const { data: intersectionLocations, isFetching: isLocationsLoading } =
    useGetIntersectionsQuery({
      routeName,
      direction,
      dateRange,
    });

  // Map location ID's to GTFS object
  const locations = useMemo(() => {
    if (!intersectionLocations?.length) return {};

    return intersectionLocations.reduce((map, intersection) => {
      const { location_id: locationId } = intersection;
      return { ...map, [locationId]: intersection };
    }, {});
  }, [intersectionLocations]);

  // Transform signal delay data to intersections with locations
  const intersections = useMemo(() => {
    if (!signalDelay?.length) return [];

    return joinMetricsIntersections({
      locations,
      metrics: signalDelay,
    });
  }, [signalDelay, locations]);

  const isLoading = useMemo(
    () => isSignalDelayLoading || isLocationsLoading,
    [isSignalDelayLoading, isLocationsLoading]
  );

  return { intersections, isLoading };
};

export default useIntersections;
