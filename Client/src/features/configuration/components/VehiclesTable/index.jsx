import React, { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { Space } from 'antd';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import openNotification from '../../../../common/components/notification';
import skeletonRelation from '../../../../templates/skeleton_relation.json';
import { useChangePreemptionMutation } from '../../api';
import { capitalizeFirstLetter } from '../../utils';
import EditVehicleModal from '../EditVehicleModal';
import MakeModel from '../MakeModel';
import ConfirmModal from '../ConfirmModal';
import './style.css';

const VehiclesTable = ({
  vehicles,
  associatedDevices,
  associatedDevicesData,
  isLoading,
  deleteVehicleResponse,
  deleteVehicle,
  editVehicleResponse,
  editVehicle,
  dissociateDeviceResponse,
  dissociateDevice,
  setDevice,
  setVehicleId,
  setEditingDevice,
  handleDeleteDeviceClick,
}) => {
  const [vehicle, setVehicle] = useState({});
  const [selectedVehicle, setSelectedVehicle] = useState([]);
  const [editingVehicle, setEditingVehicle] = useState(false);
  const [deletingVehicle, setDeletingVehicle] = useState(false);
  const [vehicleBody, setVehicleBody] = useState({});

  const [changePreemption, changePreemptionResponse] =
    useChangePreemptionMutation();

  const { region } = useSelector(({ user }) => user);
  const { agency } = useSelector(({ configuration }) => configuration);

  const { data, isSuccess, isError } = dissociateDeviceResponse;

  useEffect(() => {
    if (isSuccess) {
      openNotification({
        message: 'Success!',
        description: data,
        type: 'success',
      });
    }
  }, [data, isSuccess]);

  useEffect(() => {
    if (isError) {
      openNotification({
        message: 'Error Associating Device to Vehicle',
        description: dissociateDeviceResponse.error.message,
      });
    }
  }, [dissociateDeviceResponse.error?.message, isError]);

  // Handle edits and response changes to them
  const handleEditVehicleClick = (record) => {
    setVehicle(record);
    setEditingVehicle(true);
  };

  const handleEditDeviceClick = (record, parentVehicleId) => {
    setDevice(record);
    setVehicleId(parentVehicleId);
    setEditingDevice(true);
  };

  const onEditVehicleResponseChange = useCallback(() => {
    setEditingVehicle(false);
  }, [setEditingVehicle]);

  // Handle deletes and response changes to them
  const handleDeleteVehicleClick = (record) => {
    setSelectedVehicle([`${record.deviceId}`]);
    const body = {
      vehicles: [`${region}/${agency}/${record.deviceId}`],
    };
    setVehicleBody(body);
    setDeletingVehicle(true);
  };

  const onDeleteVehicleResponseChange = useCallback(() => {
    setDeletingVehicle(false);
    setSelectedVehicle([]);
  }, [setDeletingVehicle, setSelectedVehicle]);

  const onSelectedVehicleChange = useCallback(() => {
    setSelectedVehicle([]);
  }, [setSelectedVehicle]);

  // Handle dissociating a device from a vehicle
  const handleDissociateDeviceClick = (record, parentVehicleId) => {
    try {
      const selected = [record.deviceId];
      const vehicleName = parentVehicleId;
      const relation = {
        ...skeletonRelation,
        selected,
        vehicleName,
      };
      dissociateDevice(relation);

      if (
        'preemptionLicense' in record &&
        record.preemptionLicense !== 'inactive'
      ) {
        const devices = {
          [`${record.deviceId}`]: 'inactive',
        };

        const body = {
          agency_guid: agency.attributes.agencyID,
          devices,
        };

        changePreemption({ body });
      }
    } catch (err) {
      openNotification({
        message: 'Error associating device',
        description: err,
      });
    }
  };

  const vehiclesColumns = [
    {
      key: 'name',
      dataIndex: 'name',
      title: 'Vehicle Name',
      render: (_, record) => (
        <a onClick={() => handleEditVehicleClick(record)}>
          {record.attributes.name}
        </a>
      ),
      sorter: alphanumericSorter('attributes.name'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'description',
      dataIndex: 'description',
      title: 'Description',
      sorter: alphanumericSorter('description'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'type',
      dataIndex: 'type',
      title: 'Type',
      render: (_, { attributes }) => <p>{attributes.type}</p>,
      sorter: alphanumericSorter('attributes.type'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'priority',
      dataIndex: 'priority',
      title: 'Priority',
      render: (_, { attributes }) => <p>{attributes.priority}</p>,
      sorter: alphanumericSorter('attributes.priority'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'devices',
      dataIndex: 'devices',
      title: 'Device(s)',
      render: (_, { deviceId }) => (
        <MakeModel makeModel={associatedDevicesData[deviceId]?.devices} />
      ),
    },
    {
      key: 'preemption',
      dataIndex: 'preemptionLicense',
      title: 'Pre-emption',
      render: (_, { deviceId }) => (
        <p>
          {capitalizeFirstLetter(
            associatedDevicesData[deviceId]?.preemption || ''
          )}
        </p>
      ),
    },
    {
      key: 'VID',
      dataIndex: 'VID',
      title: 'VID',
      render: (_, { attributes }) => <p>{attributes.VID}</p>,
      sorter: alphanumericSorter('attributes.VID'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'class',
      dataIndex: 'class',
      title: 'Class',
      render: (_, { attributes }) => <p>{attributes.class}</p>,
      sorter: alphanumericSorter('attributes.class'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'actions',
      dataIndex: 'actions',
      title: 'Actions',
      fixed: 'right',
      render: (_, record) => (
        <Space size="middle">
          <a
            style={{ color: '#1890ff' }}
            onClick={() => handleEditVehicleClick(record)}
          >
            Edit
          </a>
          <a
            style={{ color: 'red' }}
            onClick={() => handleDeleteVehicleClick(record)}
          >
            Delete
          </a>
        </Space>
      ),
    },
  ];

  const associatedDevicesTable = ({ record: vehicleRecord }) => {
    const parentVehicleId = vehicleRecord.deviceId;

    const associatedDevicesColumns = [
      {
        key: 'deviceId',
        dataIndex: 'deviceId',
        title: 'Device ID',
        width: 140,
        render: (_, record) => (
          <a onClick={() => handleEditDeviceClick(record, parentVehicleId)}>
            {record.deviceId}
          </a>
        ),
        sorter: alphanumericSorter('deviceId'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'description',
        dataIndex: 'description',
        title: 'Description',
        width: 180,
        sorter: alphanumericSorter('description'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'gttSerial',
        dataIndex: 'gttSerial',
        title: 'GTT Serial',
        width: 150,
        render: (_, { attributes }) => <p>{attributes.gttSerial}</p>,
        sorter: alphanumericSorter('attributes.gttSerial'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'serial',
        dataIndex: 'serial',
        title: 'Device Serial',
        width: 140,
        render: (_, { attributes }) => <p>{attributes.serial}</p>,
        sorter: alphanumericSorter('attributes.serial'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'deviceMakeModel',
        dataIndex: 'make',
        title: 'Make & Model',
        width: 200,
        render: (_, { attributes }) => {
          const make =
            attributes?.integration === 'Whelen' &&
            attributes.make === undefined
              ? 'Whelen'
              : attributes.make;
          const model =
            attributes?.integration === 'Whelen' &&
            attributes.model === undefined
              ? 'WhelenDevice'
              : attributes.model;
          return <MakeModel makeModel={[make, model]} />;
        },
        sorter: alphanumericSorter('attributes.make'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'MAC',
        dataIndex: 'MAC',
        title: 'MAC',
        width: 140,
        render: (_, { attributes }) => <p>{attributes.addressMAC}</p>,
        sorter: alphanumericSorter('attributes.addressMAC'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'LAN',
        dataIndex: 'LAN',
        title: 'LAN',
        width: 140,
        render: (_, { attributes }) => <p>{attributes.addressLAN}</p>,
        sorter: alphanumericSorter('attributes.addressLAN'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'WAN',
        dataIndex: 'WAN',
        title: 'WAN',
        width: 140,
        render: (_, { attributes }) => <p>{attributes.addressWAN}</p>,
        sorter: alphanumericSorter('attributes.addressWAN'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'IMEI',
        dataIndex: 'IMEI',
        title: 'IMEI',
        width: 140,
        render: (_, { attributes }) => <p>{attributes.IMEI}</p>,
        sorter: alphanumericSorter('attributes.IMEI'),
        sortDirections: ['ascend', 'descend'],
      },
      {
        key: 'actions',
        dataIndex: 'actions',
        title: 'Actions',
        fixed: 'right',
        width: 199,
        render: (_, record) => (
          <Space size="middle">
            <a onClick={() => handleEditDeviceClick(record, parentVehicleId)}>
              Edit
            </a>
            <a
              style={{ color: '#faad14' }}
              onClick={() =>
                handleDissociateDeviceClick(record, parentVehicleId)
              }
            >
              Dissociate
            </a>
            <a
              style={{ color: 'red' }}
              onClick={() => handleDeleteDeviceClick(record)}
            >
              Delete
            </a>
          </Space>
        ),
      },
    ];

    return (
      <Table
        style={{ width: '1140px' }}
        className="tabs-table-associated-devices"
        columns={associatedDevicesColumns}
        dataSource={associatedDevices[parentVehicleId]}
        rowKey={(value) => value.deviceId}
        pagination={false}
        bordered={false}
        scroll={{ x: 1140 }}
      />
    );
  };

  return (
    <>
      <Table
        className="tabs-table-vehicles"
        isLoading={isLoading}
        columns={vehiclesColumns}
        expandable={{
          expandedRowRender: (record) => associatedDevicesTable({ record }),
          rowExpandable: (record) => associatedDevices[record.deviceId]?.length,
        }}
        rowKey={(value) => value.deviceId}
        dataSource={vehicles}
        pagination={true}
        bordered={false}
        scroll={{ x: 1140 }}
      />
      <EditVehicleModal
        vehicle={vehicle}
        associatedDevices={associatedDevices[vehicle.deviceId]}
        preemption={
          associatedDevicesData[vehicle.deviceId]?.preemption || 'N/A'
        }
        visible={editingVehicle}
        editVehicleResponse={editVehicleResponse}
        editVehicle={editVehicle}
        onResponseChange={onEditVehicleResponseChange}
        onCancel={() => setEditingVehicle(false)}
      />
      <ConfirmModal
        visible={deletingVehicle}
        onResponseChange={onDeleteVehicleResponseChange}
        onSelectedChange={onSelectedVehicleChange}
        body={vehicleBody}
        selected={selectedVehicle}
        response={deleteVehicleResponse}
        delete={deleteVehicle}
      />
    </>
  );
};

export default VehiclesTable;
