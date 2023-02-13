import { useDispatch } from 'react-redux';
import { useCallback } from 'react';
import { useGetDeviceQuery, useEditDeviceMutation } from '../api';
import { setDevice } from '../store/slice';

// Returns the specified Device's data and exposes methods for editing and creating a Device
const useDevice = ({ params }) => {
  const dispatch = useDispatch();

  const {
    data: device,
    isLoading,
    isError,
    error,
  } = useGetDeviceQuery({ params });

  dispatch(setDevice(device));

  const [editDevice, editDeviceResponse] = useEditDeviceMutation();

  // Invalidates Device cache upon edit
  const edit = useCallback(
    (data) => {
      editDevice(data);
    },
    [editDevice]
  );

  return {
    device,
    isLoading,
    isError,
    error,
    editDeviceResponse,
    edit,
  };
};

export default useDevice;
