import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';
import RelativeLink from '../../../../common/components/RelativeLink';
import Table from '../../../../common/components/Table';
import TableCard from '../../../../common/components/TableCard';
import TableSearch from '../../../../common/components/TableSearch';
import useRoutesSearchKeysFilter from '../../../../common/hooks/useRoutesSearchKeysFilter';
import { humanizeDecimalMinutes } from '../../../../common/utils';
import './style.css';

const missingNumericSorter = (a, b) => {
  if (a == null || Number.isNaN(+a)) return -1;
  if (b == null || Number.isNaN(+b)) return 1;

  return +a - +b;
};

const formatPercentage = (metric) => {
  const fixed = (+metric * 100).toFixed(0);
  return `${fixed}%`;
};

const TravelTimeTable = ({
  direction,
  dateRange,
  periods,
  dataSource,
  isLoading,
  ...props
}) => {
  const [searchKeys, setSearchKeys] = useState([]);
  const [sortedData, setSortedData] = useState({
    order: 'descend',
    columnKey: 'signaldelay',
  });

  const filteredRoutes = useRoutesSearchKeysFilter(searchKeys, dataSource);

  const handleChange = (pagination, filters, sorter) => {
    setSortedData(sorter);
  };

  useEffect(() => {
    setSortedData({ order: 'descend', columnKey: 'signaldelay' });
  }, [direction, dateRange, periods]);

  const routesTableHeader = [
    {
      title: 'Route Name',
      key: 'route',
      dataIndex: 'route',
      render: (routeName) => (
        <RelativeLink key={routeName} to={routeName} className="route-link">
          {`Route ${routeName}`}
        </RelativeLink>
      ),
      sorter: (a, b) =>
        a.route.localeCompare(
          b.route,
          navigator.languages[0] || navigator.language,
          { numeric: true, ignorePunctuation: true }
        ),
      sortOrder: sortedData.columnKey === 'route' && sortedData.order,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: 'Avg. Signal Delay',
      dataIndex: 'signaldelay',
      key: 'signaldelay',
      render: humanizeDecimalMinutes,
      sorter: (a, b) => missingNumericSorter(a.signaldelay, b.signaldelay),
      sortOrder: sortedData.columnKey === 'signaldelay' && sortedData.order,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: 'Signal Delay (% of Travel Time)',
      dataIndex: 'delayAsPctTravel',
      key: 'delayAsPctTravel',
      render: formatPercentage,
      sorter: (a, b) =>
        missingNumericSorter(+a.delayAsPctTravel, +b.delayAsPctTravel),
      sortOrder:
        sortedData.columnKey === 'delayAsPctTravel' && sortedData.order,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: 'Avg. Dwell Time',
      dataIndex: 'dwelltime',
      key: 'dwelltime',
      render: humanizeDecimalMinutes,
      sorter: (a, b) => missingNumericSorter(a.dwelltime, b.dwelltime),
      sortOrder: sortedData.columnKey === 'dwelltime' && sortedData.order,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: 'Avg. Drive Time',
      dataIndex: 'drivetime',
      key: 'drivetime',
      render: humanizeDecimalMinutes,
      sorter: (a, b) => missingNumericSorter(a.drivetime, b.drivetime),
      sortOrder: sortedData.columnKey === 'drivetime' && sortedData.order,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: 'Avg. Route Time',
      dataIndex: 'traveltime',
      key: 'traveltime',
      render: humanizeDecimalMinutes,
      sorter: (a, b) => missingNumericSorter(a.traveltime, b.traveltime),
      sortOrder: sortedData.columnKey === 'traveltime' && sortedData.order,
      sortDirections: ['ascend', 'descend'],
    },

    // ToDo: 18.08.2021 Uncomment when the data is available
    // {
    //   title: 'Avg. TSP savings',
    //   dataIndex: 'tspsavings',
    //   key: 'tspsavings',
    //   render: humanizeDecimalMinutes,
    //   sorter: (a, b) => parseFloat(a.tspsavings) - parseFloat(b.tspsavings),
    //   sortDirections: [ 'ascend', 'descend' ],
    // },
  ];

  return (
    <TableCard
      title="Routes"
      controls={
        isLoading || (
          <TableSearch
            data={dataSource}
            handleSearch={setSearchKeys}
            itemSearchField="route"
            searchKeys={searchKeys}
            placeholder="Enter Route"
            title="Search Routes:"
          />
        )
      }
    >
      <Table
        columns={routesTableHeader}
        dataSource={filteredRoutes}
        rowKey={(record) => `${record.route}-${record.traveltime}`}
        isLoading={isLoading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
        }}
        onChange={handleChange}
        {...props}
      />
    </TableCard>
  );
};

const mapStateToProps = ({ routeFilters }) => ({
  direction: routeFilters.direction,
  dateRange: routeFilters.dateRange,
  periods: routeFilters.periods,
});

export default connect(mapStateToProps)(TravelTimeTable);
