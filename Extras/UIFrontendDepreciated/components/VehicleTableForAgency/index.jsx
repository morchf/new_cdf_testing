import React, { useState, useEffect, useCallback } from 'react';
import { Link, withRouter } from 'react-router-dom';
import Button from '../../../../common/components/Button';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import ConfirmModal from '../ConfirmModal';
import CreateVehicle from '../CreateVehicle';
import './style.css';

const VehicleTableForAgency = (props) => {
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
  const vehicleNames = props.vehicles.map((vehicle) => vehicle.name);
  const vehicleIDs = props.vehicles.map((vehicle) => vehicle.deviceId);
  const columns = [
    {
      key: 'name',
      dataIndex: 'name',
      title: 'Name',
      render: (text) => (
        <Link
          to={`${currentPath}/vehicle/${vehicleIDs[
            vehicleNames.indexOf(text)
          ].toLowerCase()}`}
        >
          {text}
        </Link>
      ),
      sorter: alphanumericSorter('name'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'description',
      dataIndex: 'description',
      title: 'Description',
    },
    {
      key: 'type',
      dataIndex: 'type',
      title: 'Type',
    },
    {
      key: 'priority',
      dataIndex: 'priority',
      title: 'Priority',
      sorter: alphanumericSorter('priority'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'class',
      dataIndex: 'class',
      title: 'Class',
      sorter: alphanumericSorter('class'),
      sortDirections: ['ascend', 'descend'],
    },
    {
      key: 'vid',
      dataIndex: 'vid',
      title: 'VID',
      sorter: alphanumericSorter('vid'),
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
        vehicles: selected.map((vehicle) => `${region}/${agency}/${vehicle}`),
      }
    : { vehicles: [] };

  return (
    <div className="DissociateVehicleToAgency">
      <h5>Associated Vehicles</h5>

      <div className="VehicleTable">
        <Table
          rowSelection={selectRow}
          columns={columns}
          rowKey={(value) => value.deviceId}
          dataSource={props.vehicles}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            defaultPageSize: 20,
          }}
          bordered={false}
          scroll={windowSize < 1600 ? { x: 1200 } : {}}
        />
      </div>
      <CreateVehicle
        visible={creating}
        agencyGroupPath={props.agencyGroupPath}
        onResponseChange={handleResponse}
        onCancel={() => setCreating(false)}
        createVehicle={props.createVehicle}
        response={props.createVehicleResponse}
      />

      <Button
        type="primary"
        size="lg"
        location="right"
        onClick={() => setCreating(true)}
      >
        Create Vehicle
      </Button>
      {props.vehicles && props.vehicles.length > 0 && (
        <Button
          type="danger"
          size="lg"
          location="right"
          onClick={handleConfirmClick}
        >
          Delete Vehicle
        </Button>
      )}

      <ConfirmModal
        visible={deleting}
        onResponseChange={() => setDeleting(false)}
        onSelectedChange={handleSelected}
        body={body}
        selected={selected}
        delete={props.deleteVehicle}
        response={props.deleteVehicleResponse}
      />
    </div>
  );
};

export default withRouter(VehicleTableForAgency);
