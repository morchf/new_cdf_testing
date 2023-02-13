import { useMemo, useCallback } from 'react';
import {
  useGetVehiclesQuery,
  useCreateVehicleMutation,
  useEditVehicleMutation,
  useDeleteVehicleMutation,
} from '../api';

// Returns list of all Vehicles
const useVehicles = ({ params }) => {
  const {
    data: vehicles,
    isLoading,
    isError,
    error,
  } = useGetVehiclesQuery({ params });

  const vehiclesList = useMemo(
    () =>
      vehicles?.results?.reduce(
        (obj, vehicle) => ({ ...obj, [vehicle.deviceId]: vehicle }),
        {}
      ),
    [vehicles]
  );

  const vehiclesData = useMemo(
    () =>
      vehicles?.results?.map((vehicle) => ({
        deviceId: vehicle.deviceId,
        description: vehicle.description,
        name: vehicle.attributes.name,
        type: vehicle.attributes.type,
        priority: vehicle.attributes.priority,
        class: vehicle.attributes.class,
        VID: vehicle.attributes.VID,
      })),
    [vehicles]
  );

  const [create, createVehicleResponse] = useCreateVehicleMutation();

  // Invalidates Vehicle cache upon Vehicle creation
  const createVehicle = useCallback(
    (data) => {
      create(data);
    },
    [create]
  );

  const [deleteVehicleHook, deleteVehicleResponse] = useDeleteVehicleMutation();

  // Invalidates Vehicle cache upon delete
  const deleteVehicle = useCallback(
    (data) => {
      deleteVehicleHook(data);
    },
    [deleteVehicleHook]
  );

  const [editVehicle, editVehicleResponse] = useEditVehicleMutation();

  // Invalidates Vehicle cache upon edit
  const edit = useCallback(
    (data) => {
      editVehicle(data);
    },
    [editVehicle]
  );

  return {
    vehicles,
    vehiclesList,
    vehiclesData,
    isLoading,
    isError,
    error,
    createVehicleResponse,
    createVehicle,
    deleteVehicleResponse,
    deleteVehicle,
    editVehicleResponse,
    editVehicle,
  };
};

export default useVehicles;
