import { useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { useGetIntersectionsQuery } from '../api';
import { setIntersections } from '../store/slice';

const useIntersections = () => {
  const dispatch = useDispatch();

  const { data, isLoading } = useGetIntersectionsQuery();

  const intersections = useMemo(() => {
    if (isLoading || !data) return [];

    return data.map(
      ({
        latitude,
        longitude,
        intersectionName,
        intersectionId,
        serialNumber,
        make,
        model,
        ...rest
      }) => ({
        latitude,
        longitude,
        coordinates: [latitude, longitude],
        intersectionName: intersectionName.trim(),
        makeModel: [make, model],
        serialNumber,
        intersectionId: intersectionId || serialNumber,
        key: `${intersectionName.trim()}${intersectionName.trim() ? ' ' : ''}${
          intersectionId || serialNumber
        }`,
        ...rest,
      })
    );
  }, [isLoading, data]);

  dispatch(setIntersections(intersections));

  return {
    intersections,
    isLoading,
  };
};

export default useIntersections;
