import React, { useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import moment from 'moment';
import { Tabs, Space, Tag } from 'antd';
import Button from '../../../../common/components/Button';
import ConfigurationLayout from '../../../../common/layouts/ConfigurationLayout';
import Card from '../../../../common/components/Card';
import TableSearch from '../../../../common/components/TableSearch';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import AddIntersectionModal from '../../components/AddIntersectionModal';
import RelativeLink from '../../../../common/components/RelativeLink';
import { filterIntersections } from '../../utils';
import useIntersections from '../../hooks/useIntersections';
import './style.css';
import { DATE_TIME_READABLE_FORMAT } from '../../../../common/constants';

const { TabPane } = Tabs;

// Creates a span for data in the intersection column of table
const IntersectionSpan = ({ intersectionId, intersectionName, ...props }) => (
  <span className="intersection" style={{ color: 'black' }}>
    <RelativeLink to={intersectionId} {...props}>
      {intersectionName}
    </RelativeLink>
  </span>
);

const makeModelColorPicker = (entry) => {
  if (entry === 'GTT') return 'green';
  if (entry === 'Miovision') return 'orange';
  return 'lightgrey';
};

// Creates tag for data in the make/model column of table
// Calls makeModelColorPicker to determine appropriate color
const MakeModel = ({ makeModel, ...props }) => (
  <>
    {makeModel?.length &&
      makeModel.map((entry) => {
        const color = makeModelColorPicker(entry);

        return (
          <Tag color={color} key={entry} {...props}>
            {entry}
          </Tag>
        );
      })}
  </>
);

const columns = [
  {
    key: 'intersectionName',
    dataIndex: 'intersectionName',
    title: 'Intersection',
    render: (_, { intersectionId, intersectionName }) => (
      <IntersectionSpan
        intersectionId={intersectionId}
        intersectionName={intersectionName}
      />
    ),
    sorter: alphanumericSorter('intersectionName'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'serialNumber',
    dataIndex: 'serialNumber',
    title: 'Serial #',
    sorter: alphanumericSorter('serialNumber'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'coordinates',
    dataIndex: 'coordinates',
    title: 'Coordinates (Lat | Lon)',
    render: (_, { coordinates }) => {
      const [latitude, longitude] = coordinates;

      const text = latitude && longitude ? `${latitude}, ${longitude}` : null;

      return <p style={{ margin: 0 }}>{text}</p>;
    },
    sorter: alphanumericSorter('coordinates'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'unitId',
    dataIndex: 'unitId',
    title: 'Unit ID',
    sorter: alphanumericSorter('unitId'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'lastCommunicated',
    dataIndex: 'lastCommunicated',
    title: 'Last Comm',
    sorter: alphanumericSorter('lastCommunicated'),
    sortDirections: ['ascend', 'descend'],
    render: (text) => moment(text).format(DATE_TIME_READABLE_FORMAT),
  },
  {
    key: 'makeModel',
    dataIndex: 'makeModel',
    title: 'Make Model',
    render: (_, { makeModel }) => <MakeModel makeModel={makeModel} />,
    sorter: alphanumericSorter('makeModel'),
    sortDirections: ['ascend', 'descend'],
  },
  {
    key: 'availableActions',
    dataIndex: 'availableActions',
    title: 'Available Actions',
    render: (_, record) => (
      <RelativeLink to={record.intersectionId}>Edit</RelativeLink>
    ),
    sorter: alphanumericSorter('availableActions'),
    sortDirections: ['ascend', 'descend'],
  },
];

const IntersectionsTable = ({ isLoading, data }) => (
  <Table
    className="tabs-table"
    isLoading={isLoading}
    columns={columns}
    expandable={{
      expandedRowRender: (record) => (
        <p>
          Operation Mode: {record.operationMode} | Mac Address:{' '}
          {record.macAddress} | Firmware Version: {record.firmwareVersion}
        </p>
      ),
    }}
    rowKey={(value) => value.key}
    dataSource={data}
    pagination={true}
    bordered={false}
    // footer={() => (
    //   <Space size="middle">
    //     <span className="legend">Status Legend</span>
    //     <Space>
    //       <span style={{ color: 'limegreen' }}>Normal</span>
    //       <span style={{ color: 'orange' }}>Warning</span>
    //       <span style={{ color: 'red' }}>Error</span>
    //     </Space>
    //   </Space>
    // )}
  />
);

// Intersections L1 Page
const IntersectionsPage = () => {
  const [searchKeys, setSearchKeys] = useState([]);
  const [activeTab, setActiveTab] = useState('configured');
  const [adding, setAdding] = useState(false);

  const { intersections, isLoading } = useIntersections();
  const dataSource = !isLoading
    ? filterIntersections(searchKeys)(
        intersections.filter(({ isConfigured }) =>
          activeTab === 'configured' ? isConfigured : !isConfigured
        )
      )
    : [];
  const dropdownData = intersections.filter(({ isConfigured }) =>
    activeTab === 'configured' ? isConfigured : !isConfigured
  );
  useEffect(() => {
    setSearchKeys([]);
  }, []);

  const handleClick = () => {
    setAdding(true);
  };
  return (
    <ConfigurationLayout>
      <Card>
        <Tabs
          onChange={setActiveTab}
          defaultActiveKey={activeTab}
          className="tabs"
          tabBarExtraContent={
            <div className="tabs-extra-content">
              <div className="tabs-button">
                <Button
                  type="primary"
                  size=""
                  location="center"
                  onClick={handleClick}
                >
                  + Add Intersection
                </Button>
              </div>
              <div className="tabs-tablesearch">
                <TableSearch
                  data={dropdownData}
                  handleSearch={setSearchKeys}
                  itemSearchField="key"
                  searchKeys={searchKeys}
                  placeholder="Enter Intersection"
                />
              </div>
            </div>
          }
        >
          <TabPane tab="Intersections" key="configured">
            <IntersectionsTable data={dataSource} isLoading={isLoading} />
          </TabPane>
          <TabPane tab="Unassigned Hardware" key="unassigned">
            <IntersectionsTable data={dataSource} isLoading={isLoading} />
          </TabPane>
        </Tabs>
      </Card>

      <AddIntersectionModal
        visible={adding}
        onCancel={() => setAdding(false)}
      />
    </ConfigurationLayout>
  );
};

export default withRouter(IntersectionsPage);
