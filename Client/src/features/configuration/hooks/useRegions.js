import { useMemo, useCallback } from 'react';
import {
  useGetRegionsQuery,
  useCreateRegionMutation,
  useDeleteRegionMutation,
} from '../api';

// Returns list of all Regions
const useRegions = ({ params }) => {
  const { data, isLoading, isError, error } = useGetRegionsQuery({ params });

  const regions = useMemo(
    () =>
      data?.results?.map((agency) => ({
        description: agency.description,
        name: agency.name,
      })),
    [data]
  );

  const [create, createRegionResponse] = useCreateRegionMutation();

  // Invalidates Region cache upon Region creation
  const createRegion = useCallback(
    (d) => {
      create(d);
    },
    [create]
  );

  const [deleteRegionHook, deleteRegionResponse] = useDeleteRegionMutation();

  // Invalidates Region cache upon delete
  const deleteRegion = useCallback(
    (d) => {
      deleteRegionHook(d);
    },
    [deleteRegionHook]
  );

  return {
    regions,
    isLoading,
    isError,
    error,
    createRegionResponse,
    createRegion,
    deleteRegionResponse,
    deleteRegion,
  };
};

export default useRegions;
