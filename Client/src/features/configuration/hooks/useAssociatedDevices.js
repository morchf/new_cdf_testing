import { useGetAssociatedDevicesQuery } from '../api';

// Given a list of vehicle names, returns a list of the devices associated with each given vehicle
const useAssociatedDevices = (vehicleIds) => {
  const { data, isLoading, isError, error } =
    useGetAssociatedDevicesQuery(vehicleIds);

  return {
    associatedDevices: data?.associatedDevices || {},
    associatedDevicesData: data?.associatedDevicesData || {},
    isLoading,
    isError,
    error,
  };
};

export default useAssociatedDevices;
