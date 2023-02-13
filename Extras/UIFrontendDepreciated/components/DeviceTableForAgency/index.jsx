import React, { useState, useEffect, useCallback } from 'react';
import { Link, withRouter } from 'react-router-dom';
import Button from '../../../../common/components/Button';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import ConfirmModal from '../ConfirmModal';
import CreateDevice from '../CreateDevice';
import './style.css';

const DeviceTableForAgency = (props) => {
  const [selected, setSelected] = useState([]);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [windowSize, setWindowSize] = useState(undefined);

  useEffect(() => {
    const handleResize = async (e) => {
      setWindowSize(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
  }, []);

  const handleConfirmClick = () => {
    setDeleting(true);
  };

  const handleSelected = () => {
    setSelected([]);
  };

  const handleResponse = useCallback(() => {
    setCreating(false);
  }, [setCreating]);

  const currentPath = props.location.pathname;
  const columns = [
    {
      key: 'deviceId',
      dataIndex: 'deviceId',
      title: 'Device ID',
      render: (text) => (
        <Link to={`${currentPath}/device/${text.toLowerCase()}`}>{text}</Link>
      ),
      sorter: alphanumericSorter('deviceId'),
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

  const selectRow = {
    selectedRowKeys: selected,
    onChange: (selectedRowKeys) => setSelected([...selectedRowKeys]),
  };

  const region = props.match.params.regname;
  const agency = props.match.params.agyname;
  const body = selected
    ? {
        communicators: selected.map(
          (device) => `${region}/${agency}/${device}`
        ),
      }
    : { communicators: [] };

  return (
    <div className="DissociateDeviceToAgency">
      <h5>Associated Devices</h5>

      <div className="DeviceTable">
        <Table
          rowSelection={selectRow}
          columns={columns}
          rowKey={(value) => value.deviceId}
          dataSource={props.devices}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            defaultPageSize: 20,
          }}
          bordered={false}
          scroll={windowSize < 1600 ? { x: 1200 } : {}}
        />
      </div>
      <CreateDevice
        visible={creating}
        agencyGroupPath={props.agencyGroupPath}
        vehicle=""
        onResponseChange={handleResponse}
        onCancel={() => setCreating(false)}
        createDevice={props.createDevice}
        response={props.createDeviceResponse}
      />

      <Button
        type="primary"
        size="lg"
        location="right"
        onClick={() => setCreating(true)}
      >
        Create Device
      </Button>
      {props.devices && props.devices.length > 0 && (
        <Button
          type="danger"
          size="lg"
          location="right"
          onClick={handleConfirmClick}
        >
          Delete Device
        </Button>
      )}

      <ConfirmModal
        visible={deleting}
        onResponseChange={() => setDeleting(false)}
        onSelectedChange={handleSelected}
        body={body}
        selected={selected}
        delete={props.deleteDevice}
        response={props.deleteDeviceResponse}
      />
    </div>
  );
};

export default withRouter(DeviceTableForAgency);
