import { useMemo, useCallback } from 'react';
import {
  useGetDevicesQuery,
  useCreateDeviceMutation,
  useEditDeviceMutation,
  useDeleteDeviceMutation,
  useDissociateDeviceMutation,
} from '../api';

// Returns list of all Devices
const useDevices = ({ params }) => {
  const {
    data: devices,
    isLoading,
    isError,
    error,
  } = useGetDevicesQuery({ params });

  const devicesList = useMemo(
    () =>
      devices?.results?.reduce(
        (obj, device) => ({ ...obj, [device.deviceId]: device }),
        {}
      ),
    [devices]
  );

  const devicesData = useMemo(
    () =>
      devices?.results?.map((device) => ({
        deviceId: device.deviceId,
        description: device.description,
        uniqueId: device.attributes.uniqueId,
        IMEI: device.attributes.IMEI,
        addressLAN: device.attributes.addressLAN,
        addressWAN: device.attributes.addressWAN,
        addressMAC: device.attributes.addressMAC,
        serial: device.attributes.serial,
        gttSerial: device.attributes.gttSerial,
        model: device.attributes.model,
        make: device.attributes.make,
      })),
    [devices]
  );

  const [create, createDeviceResponse] = useCreateDeviceMutation();

  // Invalidates Device cache upon Device creation
  const createDevice = useCallback(
    (data) => {
      create(data);
    },
    [create]
  );

  const [editDevice, editDeviceResponse] = useEditDeviceMutation();

  // Invalidates Device cache upon edit
  const edit = useCallback(
    (data) => {
      editDevice(data);
    },
    [editDevice]
  );

  const [associate, associateResponse] = useEditDeviceMutation();

  // Edit device exposed here for purposes of associating devices from vehicle
  const associateDevice = useCallback(
    (data) => {
      associate(data);
    },
    [associate]
  );

  const [dissociate, dissociateResponse] = useDissociateDeviceMutation();

  // Invalidates Device cache upon delete
  const dissociateDevice = useCallback(
    (data) => {
      dissociate(data);
    },
    [dissociate]
  );

  const [deleteDeviceHook, deleteDeviceResponse] = useDeleteDeviceMutation();

  // Invalidates Device cache upon delete
  const deleteDevice = useCallback(
    (data) => {
      deleteDeviceHook(data);
    },
    [deleteDeviceHook]
  );

  return {
    devices,
    devicesList,
    devicesData,
    isLoading,
    isError,
    error,
    createDeviceResponse,
    createDevice,
    editDeviceResponse,
    editDevice: edit,
    associateDeviceResponse: associateResponse,
    associateDevice,
    dissociateDeviceResponse: dissociateResponse,
    dissociateDevice,
    deleteDeviceResponse,
    deleteDevice,
  };
};

export default useDevices;
