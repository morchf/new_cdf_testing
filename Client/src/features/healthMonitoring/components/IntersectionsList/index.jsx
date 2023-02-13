import { ReloadOutlined } from '@ant-design/icons';
import { Button as AntButton, Input as AntInput } from 'antd';
import { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import useSearchTermFilter from '../../../../common/hooks/useSearchTermFilter';
import { readableDateTimeFormatter } from '../../../../common/utils';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import FilterTree from '../../../../common/components/FilterTree';
import TableCard from '../../../../common/components/TableCard';
import { setFilters } from '../../store/slice';
import './style.css';
import useIntersectionsList from '../../hooks/useIntersectionsList';

const { Search: AntSearch } = AntInput;

const columns = [
  {
    dataIndex: 'locationname',
    key: 'locationname',
    title: 'Intersection Name',
    onFilter: (value, record) =>
      record.name
        ? record.name.toString().toLowerCase().includes(value.toLowerCase())
        : '',
    defaultSortOrder: 'ascend',
    sorter: alphanumericSorter('locationname'),
  },
  {
    dataIndex: 'deviceName',
    key: 'deviceName',
    title: 'Device Name',
    sorter: alphanumericSorter('deviceName'),
  },
  {
    dataIndex: 'status',
    key: 'status',
    title: 'Status',
    sorter: alphanumericSorter('status'),
    render: (text) => (
      <span className={`intersections-list__status ${text.toLowerCase()}`}>
        {text}
      </span>
    ),
    filters: [
      { text: 'Normal', value: 'normal' },
      { text: 'Warning', value: 'warning' },
      { text: 'Error', value: 'error' },
    ],
    onFilter: (value, record) => record.status.toLowerCase() === value,
  },
  {
    dataIndex: 'firmwareVersion',
    key: 'firmwareVersion',
    title: 'Firmware Version',
    sorter: alphanumericSorter('firmwareVersion'),
  },
  {
    dataIndex: 'dateLastLogRetrieved',
    key: 'dateLastLogRetrieved',
    title: 'Last Log Retrieved',
    render: (_text, record) =>
      readableDateTimeFormatter(record.dateLastLogRetrieved),
    sorter: alphanumericSorter('dateLastLogRetrieved'),
  },
  {
    dataIndex: 'channels',
    key: 'channels',
    title: 'Channels',
    sorter: alphanumericSorter('channels'),
  },
];

const IntersectionsList = ({ filters, onFiltersChange = () => {} }) => {
  const [selected, setSelected] = useState([]);
  const [searchTerm, setSearchTerm] = useState();

  const { intersections, isLoading, refresh } = useIntersectionsList();

  const filteredIntersections = useSearchTermFilter(
    searchTerm,
    intersections,
    'locationname'
  );

  const rowSelection = {
    selectedRowKeys: selected,
    onChange: (value) => setSelected([...value]),
  };

  return (
    <TableCard
      title="Intersections"
      controls={
        <div className="intersections-list__controls">
          <FilterTree filters={filters} onFiltersChange={onFiltersChange} />
          <AntSearch
            placeholder="Intersection Name"
            allowClear
            onSearch={setSearchTerm}
          />
          <div>
            <AntButton
              type="text"
              shape="circle"
              icon={<ReloadOutlined />}
              onClick={refresh}
            />
          </div>
        </div>
      }
      table={
        <Table
          className="intersections-list__table"
          pagination={{
            showSizeChanger: true,
          }}
          isLoading={isLoading}
          columns={columns}
          rowKey={(value) => value.locationname}
          dataSource={filteredIntersections}
          rowSelection={rowSelection}
        />
      }
    ></TableCard>
  );
};

const mapStateToProps = ({ healthMonitoring }) => {
  const { filters } = healthMonitoring;
  return { filters };
};

const mapDispatchToProps = {
  onFiltersChange: (filters) => async (dispatch) =>
    dispatch(setFilters(filters)),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withRouter(IntersectionsList));
