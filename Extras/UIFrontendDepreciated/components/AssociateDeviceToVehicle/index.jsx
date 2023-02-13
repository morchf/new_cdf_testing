import React, { useState, useEffect } from 'react';
import { withRouter, Link } from 'react-router-dom';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import skeletonRelation from '../../../../templates/skeleton_relation.json';
import openNotification from '../../../../common/components/notification';
import Button from '../../../../common/components/Button';
import './style.css';

const AssociateDeviceToVehicle = ({
  availableDevices,
  vehicleName,
  associateDevice,
  associateDeviceResponse,
  location,
  match,
}) => {
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [selected, setSelected] = useState([]);
  const [windowSize, setWindowSize] = useState(undefined);
  const { data, isSuccess, isError } = associateDeviceResponse;

  const handleAssociateState = () => {
    setError('');
    setSearchInput('');
    setSelected([]);
  };

  useEffect(() => {
    if (isSuccess) {
      openNotification({
        message: 'Success!',
        description: data,
        type: 'success',
      });
      handleAssociateState();
    }
  }, [data, isSuccess]);

  useEffect(() => {
    if (isError)
      openNotification({
        message: 'Error Associating Device to Vehicle',
        description: associateDeviceResponse.error.message,
      });
  }, [associateDeviceResponse.error?.message, isError]);

  useEffect(() => {
    const handleResize = async (e) => {
      setWindowSize(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
  }, []);

  const currentPath = location.pathname;
  const parentPath = currentPath.substring(0, currentPath.indexOf('/vehicle'));
  const { vehname } = match.params;
  const columns = [
    {
      key: 'key',
      dataIndex: 'deviceId',
      title: 'Device ID',
      render: (text) => (
        <Link
          to={`${parentPath}/vehicle/${vehname}/device/${text.toLowerCase()}`}
        >
          {text}
        </Link>
      ),
      sorter: alphanumericSorter('key'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'description',
      dataIndex: 'description',
      title: 'Description',
    },
    {
      key: 'gttSerial',
      dataIndex: 'gttSerial',
      title: 'GTT Serial',
      sorter: alphanumericSorter('gttSerial'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'serial',
      dataIndex: 'serial',
      title: 'Serial',
      sorter: alphanumericSorter('serial'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'addressLAN',
      dataIndex: 'addressLAN',
      title: 'LAN Address',
      sorter: alphanumericSorter('addressLAN'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'addressWAN',
      dataIndex: 'addressWAN',
      title: 'WAN Address',
      sorter: alphanumericSorter('addressWAN'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'model',
      dataIndex: 'model',
      title: 'Model',
      sorter: alphanumericSorter('model'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'make',
      dataIndex: 'make',
      title: 'Make',
      sorter: alphanumericSorter('make'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'IMEI',
      dataIndex: 'IMEI',
      title: 'IMEI',
      sorter: alphanumericSorter('IMEI'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'addressMAC',
      dataIndex: 'addressMAC',
      title: 'MAC Address',
      sorter: alphanumericSorter('addressMAC'),
      sortDirections: ['ascend', 'descend'],
    },
  ];

  const selectedRowKeys = selected;

  const selectRow = {
    selectedRowKeys,
    onChange: (keys) => {
      setSelected(keys);
    },
  };

  const handleClick = async (e) => {
    try {
      e.preventDefault();
      const relation = {
        ...skeletonRelation,
        selected,
        vehicleName,
      };
      associateDevice(relation);
    } catch (err) {
      openNotification({
        message: 'Error associating device',
        description: err,
      });
    }
  };

  function DeviceTable({ items, error: e }) {
    if (e) {
      return <p>{e}</p>;
    }
    const tableItems =
      !items || items.length === 0
        ? null
        : items.map((item) => ({
            key: item.deviceId,
            ...item,
          }));
    return (
      <div className="DeviceTable">
        <Table
          rowSelection={selectRow}
          columns={columns}
          dataSource={tableItems}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            defaultPageSize: 20,
          }}
          bordered={false}
          scroll={windowSize < 1600 ? { x: 1200 } : {}}
        />
      </div>
    );
  }
  return (
    <div className="AssociateVehicleToVehicle">
      <h5>Associate More Devices</h5>
      <DeviceTable items={availableDevices} error={error} />

      {availableDevices && availableDevices.length > 0 && (
        <Button
          type="secondary"
          size="lg"
          location="right"
          onClick={handleClick}
        >
          Associate Device
        </Button>
      )}
    </div>
  );
};

export default withRouter(AssociateDeviceToVehicle);
