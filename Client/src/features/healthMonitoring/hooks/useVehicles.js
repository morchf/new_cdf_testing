import { useGetVehiclesQuery } from '../api';

const useVehicles = () => {
  const { data: vehicles, isLoading } = useGetVehiclesQuery();

  return {
    vehicles,
    isLoading,
  };
};

export default useVehicles;
