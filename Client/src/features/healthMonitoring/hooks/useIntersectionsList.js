import { useCallback } from 'react';
import {
  useGetIntersectionsListQuery,
  useRefreshIntersectionsMutation,
} from '../api';

const useIntersectionsList = () => {
  const { data: intersections, isLoading } = useGetIntersectionsListQuery();

  // Invalidates intersections cache
  const [refreshIntersections] = useRefreshIntersectionsMutation();

  const refresh = useCallback(() => {
    refreshIntersections();
  }, [refreshIntersections]);

  return {
    intersections,
    isLoading,
    refresh,
  };
};

export default useIntersectionsList;
