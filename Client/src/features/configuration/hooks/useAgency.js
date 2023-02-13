import { useDispatch } from 'react-redux';
import { useCallback } from 'react';
import { useGetAgencyQuery, useEditAgencyMutation } from '../api';
import { setAgency } from '../store/slice';

// Returns the specified Agency's data and exposes methods for editing and creating an Agency
const useAgency = ({ params }) => {
  const dispatch = useDispatch();

  const {
    data: agency,
    isLoading,
    isError,
    error,
  } = useGetAgencyQuery({ params });

  dispatch(setAgency(agency));

  const [editAgency, editAgencyResponse] = useEditAgencyMutation();

  // Invalidates Agency cache upon edit
  const edit = useCallback(
    (data) => {
      editAgency(data);
    },
    [editAgency]
  );

  return {
    agency,
    isLoading,
    isError,
    error,
    editAgencyResponse,
    edit,
  };
};

export default useAgency;
