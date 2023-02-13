import React from 'react';
import { Space } from 'antd';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import MakeModel from '../MakeModel';
import './style.css';

const DevicesTable = ({
  devices,
  isLoading,
  setDevice,
  setVehicleId,
  setEditingDevice,
  setAssigningToVehicle,
  handleDeleteClick,
}) => {
  const handleAssignClick = (record) => {
    setDevice(record);
    setAssigningToVehicle(true);
  };

  const handleEditClick = (record) => {
    setDevice(record);
    setVehicleId('');
    setEditingDevice(true);
  };

  const devicesColumns = [
    {
      key: 'deviceId',
      dataIndex: 'deviceId',
      title: 'Device ID',
      width: 140,
      render: (_, record) => (
        <a onClick={() => handleEditClick(record)}>{record.deviceId}</a>
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
          attributes?.integration === 'Whelen' && attributes.make === undefined
            ? 'Whelen'
            : attributes.make;
        const model =
          attributes?.integration === 'Whelen' && attributes.model === undefined
            ? 'WhelenDevice'
            : attributes.model;
        return <MakeModel makeModel={[make, model]} />;
      },
      sorter: alphanumericSorter('attributes.make'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'addressMAC',
      dataIndex: 'addressMAC',
      title: 'MAC',
      width: 140,
      render: (_, { attributes }) => <p>{attributes.addressMAC}</p>,
      sorter: alphanumericSorter('attributes.addressMAC'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'addressLAN',
      dataIndex: 'addressLAN',
      title: 'LAN',
      width: 140,
      render: (_, { attributes }) => <p>{attributes.addressLAN}</p>,
      sorter: alphanumericSorter('attributes.addressLAN'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'addressWAN',
      dataIndex: 'addressWAN',
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
      width: 140,
      render: (_, record) => (
        <Space size="middle">
          <a onClick={() => handleAssignClick(record)}>Assign</a>
          <a style={{ color: 'red' }} onClick={() => handleDeleteClick(record)}>
            Delete
          </a>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Table
        className="tabs-table-devices"
        isLoading={isLoading}
        columns={devicesColumns}
        rowKey={(value) => value.deviceId}
        dataSource={devices}
        pagination={true}
        bordered={false}
        scroll={{ x: 1140 }}
      />
    </>
  );
};

export default DevicesTable;
