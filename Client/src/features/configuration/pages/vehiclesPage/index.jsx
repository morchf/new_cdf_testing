import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSelector } from 'react-redux';
import { Tabs } from 'antd';
import openNotification from '../../../../common/components/notification';
import Button from '../../../../common/components/Button';
import ConfigurationLayout from '../../../../common/layouts/ConfigurationLayout';
import Card from '../../../../common/components/Card';
import TableSearch from '../../../../common/components/TableSearch';
import VehiclesTable from '../../components/VehiclesTable';
import DevicesTable from '../../components/DevicesTable';
import CreateVehicle from '../../components/CreateVehicle';
import CreateDevice from '../../components/CreateDevice';
import EditDeviceModal from '../../components/EditDeviceModal';
import ConfirmModal from '../../components/ConfirmModal';
import VehicleAssignmentModal from '../../components/VehicleAssignmentModal';
import useAgency from '../../hooks/useAgency';
import useVehicles from '../../hooks/useVehicles';
import useDevices from '../../hooks/useDevices';
import useAssociatedDevices from '../../hooks/useAssociatedDevices';
import useAvailableDevices from '../../hooks/useAvailableDevices';
import { filterVehicles, filterUnassignedDevices } from '../../utils';
import './style.css';

const { TabPane } = Tabs;

// Vehicle Configuration L1 page
const VehiclesPage = () => {
  // Current tab state
  const [currentTab, setCurrentTab] = useState('Vehicles');

  // Search Keys
  const [vehiclesSearchKeys, setVehiclesSearchKeys] = useState([]);
  const [devicesSearchKeys, setDevicesSearchKeys] = useState([]);

  // Vehicle state methods
  const [creatingVehicle, setCreatingVehicle] = useState(false);

  // Device state methods
  const [creatingDevice, setCreatingDevice] = useState(false);
  const [editingDevice, setEditingDevice] = useState(false);
  const [deletingDevice, setDeletingDevice] = useState(false);
  const [assigningToVehicle, setAssigningToVehicle] = useState(false);
  const [vehicleId, setVehicleId] = useState('');

  // Auxiliary state methods for editing and deleting devices
  const [device, setDevice] = useState({});
  const [selectedDevice, setSelectedDevice] = useState([]);
  const [deviceBody, setDeviceBody] = useState({});

  const { region: regname, agency: agyname } = useSelector(({ user }) => user);

  // load agency data
  let params = `/groups/%2F${regname}%2F${agyname}`;
  const { agency } = useAgency({ params });

  // load vehicles data
  params = `/groups/%2F${regname}%2F${agyname}/members/devices?template=vehicleV2`;
  const {
    vehicles,
    vehiclesList,
    vehiclesData: vd,
    isLoading: vehiclesIsLoading,
    isError: vehiclesIsError,
    error: vehiclesError,
    createVehicleResponse,
    createVehicle,
    deleteVehicleResponse,
    deleteVehicle,
    editVehicleResponse,
    editVehicle,
  } = useVehicles({ params });

  useEffect(() => {
    if (vehiclesIsError)
      openNotification({
        message: 'Error Getting Vehicles Data',
        description: vehiclesError.message,
      });
  }, [vehiclesError?.message, vehiclesIsError]);

  // load all communicator devices of the agency
  params = `/groups/%2F${regname}%2F${agyname}/ownedby/devices?template=communicator`;
  const {
    devices: communicators,
    isLoading: communicatorsIsLoading,
    isError: communicatorsIsError,
    error: communicatorsError,
    createDeviceResponse,
    createDevice,
    editDeviceResponse,
    editDevice,
    associateDeviceResponse,
    associateDevice,
    dissociateDeviceResponse,
    dissociateDevice,
    deleteDeviceResponse,
    deleteDevice,
  } = useDevices({ params });

  useEffect(() => {
    if (communicatorsIsError)
      openNotification({
        message: 'Error Getting Communicator Devices',
        description: communicatorsError.message,
      });
  }, [communicatorsError?.message, communicatorsIsError]);

  // load all integrationcom devices of the agency
  params = `/groups/%2F${regname}%2F${agyname}/ownedby/devices?template=integrationcom`;
  const {
    devices: integrationcoms,
    isLoading: integrationscomsIsLoading,
    isError: integrationscomsIsError,
    error: integrationscomsError,
  } = useDevices({ params });

  useEffect(() => {
    if (integrationscomsIsError)
      openNotification({
        message: 'Error Getting Integration Com Devices',
        description: integrationscomsError.message,
      });
  }, [integrationscomsError?.message, integrationscomsIsError]);

  /** @TODO Update useAssociatedDevices with new endpoint once CDF migration complete. See TODO's in configuration/api/index.js */
  // for endpoints that need to be updated
  // Create a list of vehicle ID's, then get a list of devices associated with each vehicle
  const vehicleIds = vehiclesList ? Object.keys(vehiclesList) : null;
  const {
    associatedDevices,
    associatedDevicesData,
    isLoading: associatedDevicesIsLoading,
    isError: associatedDevicesIsError,
    error: associatedDevicesError,
  } = useAssociatedDevices(vehicleIds);

  useEffect(() => {
    if (associatedDevicesIsError)
      openNotification({
        message: 'Error Getting Associated Devices',
        description: associatedDevicesError.message,
      });
  }, [associatedDevicesError?.message, associatedDevicesIsError]);

  /** @TODO Update useAvailableDevices with new endpoint once CDF migration complete. See TODO's in configuration/api/index.js */
  // for endpoints that need to be updated
  // Create a list of all devices under the agency, then retrieve devices not yet associated to a vehicle
  // const agencyDevices = communicators?.results.concat(integrationcoms?.result);
  const agencyDevices = useMemo(() => {
    if (communicatorsIsLoading || integrationscomsIsLoading) return [];
    return communicators.results.concat(integrationcoms.results);
  }, [
    communicators,
    communicatorsIsLoading,
    integrationcoms,
    integrationscomsIsLoading,
  ]);

  const agencyDevicesNames = agencyDevices
    ? Object.values(agencyDevices).map((agencyDevice) => agencyDevice?.deviceId)
    : null;

  const {
    data: availableDevices,
    isLoading: availableDevicesIsLoading,
    isError: availableDevicesIsError,
    error: availableDevicesError,
  } = useAvailableDevices(agencyDevicesNames);

  useEffect(() => {
    if (availableDevicesIsError)
      openNotification({
        message: 'Error Getting Unassigned Devices',
        description: availableDevicesError.message,
      });
  }, [availableDevicesError?.message, availableDevicesIsError]);

  // Make sure all data is loaded before displaying any tables
  const isLoading = useMemo(
    () =>
      vehiclesIsLoading ||
      communicatorsIsLoading ||
      integrationscomsIsLoading ||
      associatedDevicesIsLoading ||
      availableDevicesIsLoading,
    [
      vehiclesIsLoading,
      communicatorsIsLoading,
      integrationscomsIsLoading,
      associatedDevicesIsLoading,
      availableDevicesIsLoading,
    ]
  );

  // Set up filtering for vehicles and devices so user can search in tables
  const vehiclesData = !vehiclesIsLoading
    ? filterVehicles(vehiclesSearchKeys)(vehicles.results)
    : null;

  const devicesData = !communicatorsIsLoading
    ? filterUnassignedDevices(devicesSearchKeys)(availableDevices)
    : null;

  // Callbacks for creating vehicles and devices
  const onCreateVehicleResponseChange = useCallback(() => {
    setCreatingVehicle(false);
  }, [setCreatingVehicle]);

  const onCreateDeviceResponseChange = useCallback(() => {
    setCreatingDevice(false);
  }, [setCreatingDevice]);

  // Callback for handling device edit response
  const onEditDeviceResponseChange = useCallback(() => {
    setEditingDevice(false);
  }, [setEditingDevice]);

  // Callback for handling response from associating a device to a vehicle
  const onVehicleAssignmentResponseChange = useCallback(() => {
    setAssigningToVehicle(false);
  }, [setAssigningToVehicle]);

  // Callback for handling deleting a device
  const onDeleteDeviceResponseChange = useCallback(() => {
    setDeletingDevice(false);
    setSelectedDevice([]);
  }, [setDeletingDevice, setSelectedDevice]);

  // Callback for updating the selected device for ConfirmModal
  const onSelectedDeviceChange = useCallback(() => {
    setSelectedDevice([]);
  }, [setSelectedDevice]);

  // Callback for triggering ConfirmModal
  const handleDeleteClick = useCallback(
    (record) => {
      const { deviceId } = record;
      setSelectedDevice([`${deviceId}`]);
      const body = {
        communicators: [`${regname}/${agyname}/${deviceId}`],
      };
      setDeviceBody(body);
      setDeletingDevice(true);
    },
    [setSelectedDevice, setDeviceBody, setDeletingDevice, regname, agyname]
  );

  // Based on which tab is currently open, display the correct modal for creating a vehicle or device
  const handleClick = () => {
    if (currentTab === 'Vehicles') setCreatingVehicle(true);
    else setCreatingDevice(true);
  };

  return (
    <ConfigurationLayout>
      <Card>
        <Tabs
          className="tabs"
          onTabClick={(selectedKey) => setCurrentTab(selectedKey)}
          tabBarExtraContent={
            <div className="tabs-extra-content">
              <div className="tabs-button">
                <Button
                  type="primary"
                  size=""
                  location="center"
                  onClick={() => handleClick(true)}
                >
                  + Create New{' '}
                  {currentTab === 'Vehicles' ? 'Vehicle' : 'Device'}
                </Button>
              </div>
              <div className="tabs-tablesearch">
                {currentTab === 'Vehicles' ? (
                  <TableSearch
                    data={vd}
                    handleSearch={setVehiclesSearchKeys}
                    itemSearchField="name"
                    searchKeys={vehiclesSearchKeys}
                    placeholder="Enter Vehicle"
                  />
                ) : (
                  <TableSearch
                    data={availableDevices}
                    handleSearch={setDevicesSearchKeys}
                    itemSearchField="deviceId"
                    searchKeys={devicesSearchKeys}
                    placeholder="Enter Device"
                  />
                )}
              </div>
            </div>
          }
        >
          <TabPane tab="Vehicles" key="Vehicles">
            <VehiclesTable
              vehicles={vehiclesData}
              associatedDevices={associatedDevices}
              associatedDevicesData={associatedDevicesData}
              isLoading={isLoading}
              deleteVehicleResponse={deleteVehicleResponse}
              deleteVehicle={deleteVehicle}
              editVehicleResponse={editVehicleResponse}
              editVehicle={editVehicle}
              dissociateDeviceResponse={dissociateDeviceResponse}
              dissociateDevice={dissociateDevice}
              setDevice={setDevice}
              setVehicleId={setVehicleId}
              setEditingDevice={setEditingDevice}
              handleDeleteDeviceClick={handleDeleteClick}
            />
          </TabPane>
          <TabPane tab="Unassigned Devices" key="Unassigned Devices">
            <DevicesTable
              devices={devicesData}
              isLoading={isLoading}
              setDevice={setDevice}
              setVehicleId={setVehicleId}
              setEditingDevice={setEditingDevice}
              setAssigningToVehicle={setAssigningToVehicle}
              handleDeleteClick={handleDeleteClick}
            />
          </TabPane>
        </Tabs>
      </Card>
      <CreateVehicle
        visible={creatingVehicle}
        agencyGroupPath={agency?.groupPath}
        onResponseChange={onCreateVehicleResponseChange}
        onCancel={() => setCreatingVehicle(false)}
        createVehicle={createVehicle}
        response={createVehicleResponse}
      />
      <CreateDevice
        visible={creatingDevice}
        agencyGroupPath={agency ? agency.groupPath : ''}
        vehicle={''}
        onResponseChange={onCreateDeviceResponseChange}
        onCancel={() => setCreatingDevice(false)}
        createDevice={createDevice}
        response={createDeviceResponse}
      />
      <EditDeviceModal
        device={device}
        vehicle={vehicleId}
        visible={editingDevice}
        editDeviceResponse={editDeviceResponse}
        editDevice={editDevice}
        onResponseChange={onEditDeviceResponseChange}
        onCancel={() => setEditingDevice(false)}
      />
      <VehicleAssignmentModal
        visible={assigningToVehicle}
        onResponseChange={onVehicleAssignmentResponseChange}
        onCancel={() => setAssigningToVehicle(false)}
        vehiclesList={vehiclesList || {}}
        editVehicle={editVehicle}
        device={device}
        editDevice={editDevice}
        associateDeviceResponse={associateDeviceResponse}
        associateDevice={associateDevice}
      />
      <ConfirmModal
        visible={deletingDevice}
        onResponseChange={onDeleteDeviceResponseChange}
        onSelectedChange={onSelectedDeviceChange}
        body={deviceBody}
        selected={selectedDevice}
        response={deleteDeviceResponse}
        delete={deleteDevice}
      />
    </ConfigurationLayout>
  );
};

export default VehiclesPage;
