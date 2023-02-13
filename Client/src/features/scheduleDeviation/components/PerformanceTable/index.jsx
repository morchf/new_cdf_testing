import React from 'react';
import { connect } from 'react-redux';
import { Table, Empty } from 'antd';
import RelativeLink from '../../../../common/components/RelativeLink';
import Skeleton from '../../../../common/components/Skeleton';
import InfoTooltip from '../../../../common/components/InfoTooltip';
import {
  capitalize1stLetter,
  humanizeDeviationLabel,
} from '../../../../common/utils';
import './style.css';

const PerformanceTable = ({
  className = '',
  isLoading = false,
  summaryCategory = [],
  title = 'Title',
  tooltip,
}) => {
  const firstTwoCategoryItems = summaryCategory?.routes?.slice(0, 2);
  const tableData = firstTwoCategoryItems?.length
    ? firstTwoCategoryItems.map(
        ({ route, direction, onTimePercentage, avgScheduleDeviation }) => ({
          route,
          direction: capitalize1stLetter(direction),
          onTime: `${(parseFloat(onTimePercentage) * 100).toFixed(0)}%`,
          avgScheduleDeviation: humanizeDeviationLabel(avgScheduleDeviation),
        })
      )
    : [];

  const classes = `scheduleDev-performance ${className}`;

  if (isLoading) {
    return (
      <div className={classes}>
        <Skeleton />
      </div>
    );
  }

  if (!firstTwoCategoryItems?.length) {
    return (
      <div className={classes}>
        <div className="top-row">{title}</div>
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} className="nodata-row" />
      </div>
    );
  }

  const columns = [
    {
      title: () => (
        <div className="top-row">
          <span>{title}</span>
          <InfoTooltip className="top-row__tooltip" text={tooltip} />
        </div>
      ),
      dataIndex: 'route',
      key: 'route',
      render: (text, item) => (
        <RelativeLink key={text} className="route-link" to={text}>
          Route {text}
        </RelativeLink>
      ),
    },

    {
      title: 'On-time',
      dataIndex: 'onTime',
      key: 'onTimePercentage',
      align: 'right',
    },
    {
      title: 'Avg. Deviation',
      key: 'avgScheduleDeviation',
      dataIndex: 'avgScheduleDeviation',
      align: 'right',
    },
  ];

  return (
    <div className={classes}>
      <Table
        columns={columns}
        dataSource={tableData}
        pagination={false}
        bordered={false}
        rowKey={(record) => `${record.route}-${record.onTimePercentage}`}
      />
    </div>
  );
};

const mapStateToProps = ({ routeFilters }) => ({
  filters: routeFilters,
});

export default connect(mapStateToProps)(PerformanceTable);
