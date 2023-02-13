import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useGetSegmentMetricsQuery } from '../api';
import { leftJoin } from '../pages/routeDetails/shapes';
import { joinSignalDelayMetricsSegments } from '../../../common/utils/shapes';
import { selectTimeperiod } from '../../featurePersistence/store/selectors';
import { LOW_CONFIDENCE_THRESHOLD } from '../constants';
import useRoutes from './useRoutes';
import useIntersections from './useIntersections';

const findAngleAtClosestPoint = ({ lat, lon }, points) => {
  if (!points?.length) return 0;

  let minDistance;
  let minAngle;

  for (let i = 0; i < points.length; i += 1) {
    const [currLat, currLon] = points[i][0];
    const distance = (currLat - lat) ** 2 + (currLon - lon) ** 2;

    if (!minDistance || distance < minDistance) {
      minDistance = distance;
      [, minAngle] = points[i];
    }
  }

  return minAngle;
};

/**
 * NOTE: Unused but left for future use
 * Create a gradient function mapping a latitude/longitude pair to the angle of
 * the route segment
 */
const createGradient = (points) => {
  const gradientPoints = [];
  points.forEach(({ lat, lon }, index) => {
    if (index === 0 || index === points.length - 1) {
      return;
    }

    const nextPoint = points[index + 1];
    const prevPoint = points[index - 1];

    const nextAngle = Math.atan2(+nextPoint.lon - +lon, +nextPoint.lat - +lat);
    const prevAngle = Math.atan2(+lon - +prevPoint.lon, +lat - +prevPoint.lat);

    gradientPoints.push([[lat, lon], (nextAngle + prevAngle) / 2]);
  });

  return (point) => findAngleAtClosestPoint(point, gradientPoints);
};

const useMap = ({ routeName, totalTrips }) => {
  const { dateRange, direction, periods } = useSelector(
    ({ routeFilters }) => routeFilters
  );
  const timeperiod = useSelector(selectTimeperiod);

  const { data: map, isFetching: isSegmentsLoading } =
    useGetSegmentMetricsQuery({
      routeName,
      dateRange,
      direction,
      periods,
      timeperiod,
    });

  const { selectedRoute, isLoading: isRoutesLoading } = useRoutes({
    routeName,
  });

  // Join map data with segment metrics
  const stops = useMemo(
    () =>
      selectedRoute?.segments?.length && map
        ? (
            joinSignalDelayMetricsSegments(
              selectedRoute.segments,
              map,
              leftJoin
            ) || []
          ).map((item, index) =>
            item ? { ...item, stopNumber: index + 1 } : item
          )
        : [],
    [selectedRoute, map]
  );

  const { intersections, isLoading: isIntersectionsLoading } = useIntersections(
    { routeName }
  );

  const lowConfidenceStops = stops.filter(
    (stop) => stop.numTrips < LOW_CONFIDENCE_THRESHOLD * totalTrips
  );

  const lowConfidenceIntersections = intersections.filter(
    (intersection) =>
      intersection.numTrips < LOW_CONFIDENCE_THRESHOLD * totalTrips
  );

  const isLoading = useMemo(
    () => isSegmentsLoading || isRoutesLoading || isIntersectionsLoading,
    [isSegmentsLoading, isRoutesLoading, isIntersectionsLoading]
  );

  return {
    map,
    stops,
    intersections,
    lowConfidenceStops,
    lowConfidenceIntersections,
    selectedRoute,
    isLoading,
  };
};

export default useMap;
