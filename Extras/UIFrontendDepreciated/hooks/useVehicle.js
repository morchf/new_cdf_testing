import { useDispatch } from 'react-redux';
import { useCallback } from 'react';
import { useGetVehicleQuery, useEditVehicleMutation } from '../api';
import { setVehicle } from '../store/slice';

// Returns the specified Vehicle's data and exposes methods for editing and creating an Vehicle
const useVehicle = ({ params }) => {
  const dispatch = useDispatch();

  const {
    data: vehicle,
    isLoading,
    isError,
    error,
  } = useGetVehicleQuery({ params });

  dispatch(setVehicle(vehicle));

  const [editVehicle, editVehicleResponse] = useEditVehicleMutation();

  // Invalidates Vehicle cache upon edit
  const edit = useCallback(
    (data) => {
      editVehicle(data);
    },
    [editVehicle]
  );

  return {
    vehicle,
    isLoading,
    isError,
    error,
    editVehicleResponse,
    edit,
  };
};

export default useVehicle;
