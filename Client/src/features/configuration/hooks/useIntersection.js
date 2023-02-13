import { useCallback, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import {
  useGetIntersectionQuery,
  useUpdateIntersectionMutation,
  useRefreshIntersectionMutation,
} from '../api';
import { setIntersection } from '../store/slice';

const useIntersection = ({ intersectionId }) => {
  const dispatch = useDispatch();

  const { data, isFetching } = useGetIntersectionQuery({
    intersectionId,
  });
  const [
    updateIntersection,
    { error: updateIntersectionError, isLoading: isUpdating, ...rest },
  ] = useUpdateIntersectionMutation();

  const [refresh] = useRefreshIntersectionMutation();

  const update = useCallback(
    (i) => {
      updateIntersection({ intersection: i });
    },
    [updateIntersection]
  );

  const isLoading = useMemo(
    () => isFetching || isUpdating,
    [isFetching, isUpdating]
  );

  const intersection = useMemo(() => {
    if (isLoading) return data;
    return { ...data, locationType: data?.locationType?.toUpperCase() };
  }, [data, isLoading]);

  dispatch(setIntersection(intersection));

  return {
    intersection,
    update,
    refresh,
    updateError: updateIntersectionError,
    isLoading,
  };
};

export default useIntersection;
