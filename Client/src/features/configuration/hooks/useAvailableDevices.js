import { useGetAvailableDevicesQuery } from '../api';

// Returns the specified Device's data and exposes methods for editing and creating a Device
const useAvailableDevices = (agencyDevicesNames) => {
  const { data, isLoading, isError, error } =
    useGetAvailableDevicesQuery(agencyDevicesNames);

  return {
    data,
    isLoading,
    isError,
    error,
  };
};

export default useAvailableDevices;
