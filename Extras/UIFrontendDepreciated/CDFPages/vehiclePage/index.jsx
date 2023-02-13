import React, { useEffect, useState } from "react";
import { connect, useDispatch } from "react-redux";
import { withRouter } from "react-router-dom";
import AssociateDeviceToVehicle from "../../components/AssociateDeviceToVehicle";
import DeviceTableForVehicle from "../../components/DeviceTableForVehicle";
import EditVehicle from "../../components/EditVehicle";
import openNotification from "../../../../common/components/notification";
import useVehicle from "../../hooks/useVehicle";
import useDevices from "../../hooks/useDevices";
import useAvailableDevices from "../../hooks/useAvailableDevices";
import api from "../../api";
import ConfigurationLayout from "../../../../common/layouts/ConfigurationLayout";
import "./style.css";

const transformDevices = (devices) =>
  devices.map((device) => ({
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
  }));

const VehiclePage = ({ admin, match, getDevice }) => {
  const { regname } = match.params;
  const { agyname } = match.params;
  const { vehname } = match.params;

  const [devices, setDevices] = useState(null);
  const [available, setAvailableDevices] = useState(undefined);

  // load vehicle data
  let params = `/devices/${vehname}`;
  const {
    vehicle,
    isError: vehicleIsError,
    error: vehicleError,
    editVehicleResponse,
    edit: editVehicle,
  } = useVehicle({ params });

  // load all devices of the agency and filter those haven't yet been installed at any vehicle
  params = `/groups/%2F${regname}%2F${agyname}/ownedby/devices?template=communicator`;
  const {
    devices: agencyDevices,
    isError: agencyDevicesIsError,
    error: agencyDevicesError,
  } = useDevices({ params });

  const agencyDevicesNames = agencyDevices
    ? Object.values(agencyDevices.results).map((device) => device.deviceId)
    : null;
  const { data: availableDevices } = useAvailableDevices(agencyDevicesNames);

  // load devices associated with the vehicle
  params = `/devices/${vehname}/installedat/devices`;
  const {
    devices: vehicleDevices,
    isError: vehicleDevicesIsError,
    error: vehicleDevicesError,
    createDeviceResponse,
    createDevice,
    associateDeviceResponse,
    associateDevice,
    dissociateDeviceResponse,
    dissociateDevice,
    deleteDeviceResponse,
    deleteDevice,
  } = useDevices({ params });

  useEffect(() => {
    if (agencyDevicesIsError)
      openNotification({
        message: "Error Getting Agency Devices",
        description: agencyDevicesError.message,
      });
  }, [agencyDevicesError?.message, agencyDevicesIsError]);

  useEffect(() => {
    if (vehicleIsError)
      openNotification({
        message: "Error Getting Vehicles",
        description: vehicleError.message,
      });
  }, [vehicleError?.message, vehicleIsError]);

  useEffect(() => {
    if (vehicleDevicesIsError)
      openNotification({
        message: "Error Getting Vehicle Devices",
        description: vehicleDevicesError.message,
      });
  }, [vehicleDevicesError?.message, vehicleDevicesIsError]);

  useEffect(() => {
    if (agencyDevices && vehicleDevices && availableDevices) {
      setAvailableDevices(transformDevices(availableDevices));
      setDevices(transformDevices(vehicleDevices.results));
    }
  }, [agencyDevices, vehicleDevices, availableDevices]);

  return (
    <ConfigurationLayout
      title={vehicle ? vehicle.attributes.name : ""}
      vehicle={vehicle ? vehicle.attributes.name : ""}
    >
      <EditVehicle
        vehicle={vehicle || ""}
        editVehicle={editVehicle}
        response={editVehicleResponse}
      />
      <DeviceTableForVehicle
        agencyGroupPath={`/${regname}/${agyname}`}
        vehicleName={vehicle ? vehicle.deviceId : ""}
        devices={devices || ""}
        createDevice={createDevice}
        createDeviceResponse={createDeviceResponse}
        dissociateDevice={dissociateDevice}
        dissociateDeviceResponse={dissociateDeviceResponse}
        deleteDevice={deleteDevice}
        deleteDeviceResponse={deleteDeviceResponse}
      />
      <AssociateDeviceToVehicle
        availableDevices={available}
        vehicleName={vehicle ? vehicle.deviceId : ""}
        associateDevice={associateDevice}
        associateDeviceResponse={associateDeviceResponse}
      />
    </ConfigurationLayout>
  );
};

const mapStateToProps = (state) => ({
  admin: state.user.admin,
});
const mapDispatchToProps = {
  getDevice: api.endpoints.getDevice.initiate,
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withRouter(VehiclePage));
