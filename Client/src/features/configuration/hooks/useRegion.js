import { useCallback } from 'react';
import { useGetRegionQuery, useEditRegionMutation } from '../api';

// Returns the specified Region's data and exposes methods for editing and creating an Region
const useRegion = ({ params }) => {
  const {
    data: region,
    isLoading,
    isError,
    error,
  } = useGetRegionQuery({ params });

  const [editRegion, editRegionResponse] = useEditRegionMutation();

  // Invalidates Region cache upon edit
  const edit = useCallback(
    (data) => {
      editRegion(data);
    },
    [editRegion]
  );

  return {
    region,
    isLoading,
    isError,
    error,
    editRegionResponse,
    edit,
  };
};

export default useRegion;
