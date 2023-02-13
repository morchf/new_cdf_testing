import React from 'react';
import { connect } from 'react-redux';
import RelativeLink from '../../../../common/components/RelativeLink';
import Skeleton from '../../../../common/components/Skeleton';
import Table from '../../../../common/components/Table';
import './style.css';

const wholeNumberFormatter = (number) => Number((+number).toFixed(0));

const columns = [
  {
    title: 'Route',
    dataIndex: 'routeText',
    align: 'left',
    width: '50%',
    key: 'routeText',
    render: (text, item) => (
      <RelativeLink className="route-link" to={item.route}>
        {text}
      </RelativeLink>
    ),
  },
  {
    title: 'Delay',
    dataIndex: 'signaldelay',
    key: 'signaldelay',
    align: 'right',
    render: wholeNumberFormatter,
  },
  {
    title: 'Dwell',
    key: 'dwelltime',
    dataIndex: 'dwelltime',
    align: 'right',
    render: wholeNumberFormatter,
  },
  {
    title: 'Drive',
    key: 'drivetime',
    dataIndex: 'drivetime',
    align: 'right',
    render: wholeNumberFormatter,
  },
  {
    title: 'Total',
    key: 'sumMetrics',
    dataIndex: 'sumMetrics',
    align: 'right',
    width: '20%',
  },
];

const formatPerformanceTableData = (data = [], direction) =>
  data.map(
    ({
      signaldelay,
      drivetime,
      dwelltime,
      traveltime,
      route: routeName,
      direction: routeDirection,
      ...rest
    }) => {
      const metrics = [signaldelay, drivetime, dwelltime];
      const wholeMetrics = metrics.map((metric) =>
        wholeNumberFormatter(metric)
      );
      const sumMetrics = wholeMetrics.reduce((a, b) => a + b);
      const routeText = `Route ${routeName}`;
      return {
        signaldelay,
        drivetime,
        dwelltime,
        sumMetrics,
        routeText,
        route: routeName,
        direction,
        ...rest,
      };
    }
  );

const PerformanceTable = ({ isLoading = false, direction, routes }) => {
  const tableData = formatPerformanceTableData(routes, direction);

  return !isLoading ? (
    <div className="performance-table">
      <Table
        columns={columns}
        dataSource={tableData}
        pagination={false}
        bordered={false}
        size="small"
        rowKey={(record) => record.routeText}
      />
      <div className="performance-table__time-notes">
        <span className="performance-table__time-note">
          All Times in Minutes
        </span>
      </div>
    </div>
  ) : (
    <Skeleton className="performance-table__skeleton" active={isLoading} />
  );
};

const mapStateToProps = ({ routeFilters }) => ({
  direction: routeFilters?.direction,
});

export default connect(mapStateToProps)(PerformanceTable);
