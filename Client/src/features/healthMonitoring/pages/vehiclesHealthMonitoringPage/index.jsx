import React, { useState, useEffect } from 'react';
import HealthMonitoringLayout from '../../../../common/layouts/HealthMonitoringLayout';
import TableCard from '../../../../common/components/TableCard';
import Button from '../../../../common/components/Button';
import TableSearch from '../../../../common/components/TableSearch';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import useVehicles from '../../hooks/useVehicles';
import { filterVehicles } from '../../utils';
import { TooltipText } from '../../constants';
import './style.css';

const Metrics = ({ numVehiclesInCommunication, numVehiclesInSystem }) => (
  <div className="vehicles-health-monitoring-metrics">
    <div>
      <h2>Vehicles</h2>
      <p className="vehicles-health-monitoring-metrics-num">
        {numVehiclesInCommunication}
      </p>
      <p>in communication</p>
    </div>
    <div>
      <h2 className="vehicles-health-monitoring-metrics-in-system">Vehicles</h2>
      <p className="vehicles-health-monitoring-metrics-num vehicles-health-monitoring-metrics-in-system">
        {numVehiclesInSystem}
      </p>
      <p className="vehicles-health-monitoring-metrics-in-system">in system</p>
    </div>
  </div>
);

const Title = ({ timeStamp }) => <p>Updated {timeStamp}</p>;

const columns = [
  {
    key: 'name',
    dataIndex: 'name',
    title: 'Vehicle',
    sorter: alphanumericSorter('name'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'lastHeard',
    dataIndex: 'lastHeard',
    title: 'Last Heard Timestamp',
    sorter: alphanumericSorter('lastHeard'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'daysSinceLastHeard',
    dataIndex: 'daysSinceLastHeard',
    title: 'Days Since Last Heard',
    sorter: alphanumericSorter('daysSinceLastHeard'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'intersection',
    dataIndex: 'intersection',
    title: 'Last Intersection',
    sorter: alphanumericSorter('intersection'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'firmware',
    dataIndex: 'firmware',
    title: 'Firmware',
    sorter: alphanumericSorter('firmware'),
    sortDirections: ['ascend', 'descend'],
  },
];

const VehiclesTable = ({ isLoading, data }) => (
  <Table
    className="vehicles-health-monitoring-table"
    isLoading={isLoading}
    columns={columns}
    expandable={{
      expandedRowRender: (record) => (
        <p className="vehicles-health-monitoring-table-expanded">
          Device: {record.device} &nbsp; | &nbsp; SN: {record.serial} &nbsp; |
          &nbsp; Telematics: {record.telematics} &nbsp; | &nbsp; Class:{' '}
          {record.class} &nbsp; | &nbsp; Registered: {record.registered}
        </p>
      ),
    }}
    rowKey={(value) => value.name}
    dataSource={data}
    pagination={true}
    bordered={false}
  />
);

const VehiclesHealthMonitoringPage = () => {
  const [searchKeys, setSearchKeys] = useState([]);

  const { vehicles, isLoading } = useVehicles();

  // Set up filtering for vehicles so user can search in tables
  const data = !isLoading ? filterVehicles(searchKeys)(vehicles) : null;

  useEffect(() => {
    setSearchKeys([]);
  }, []);

  return (
    <HealthMonitoringLayout
      title={'Health Monitoring'}
      tooltip={TooltipText.HealthMonitoring}
      metrics={
        <Metrics numVehiclesInCommunication={85} numVehiclesInSystem={124} />
      }
    >
      <div className="vehicles-health-monitoring-content">
        <TableCard
          title={<Title timeStamp={'10/23/22 at 10:30 am'} />}
          controls={
            <>
              {isLoading || (
                <>
                  <Button>Refresh View</Button>
                  <TableSearch
                    data={vehicles}
                    handleSearch={setSearchKeys}
                    itemSearchField="name"
                    searchKeys={searchKeys}
                    placeholder="Enter Vehicle"
                  />
                </>
              )}
            </>
          }
          table={<VehiclesTable isLoading={isLoading} data={data} />}
        />
      </div>
    </HealthMonitoringLayout>
  );
};

export default VehiclesHealthMonitoringPage;
