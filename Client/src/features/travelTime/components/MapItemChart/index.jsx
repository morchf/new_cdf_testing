import React from 'react';
import moment from 'moment';
import Draggable from 'react-draggable';
import { Card } from 'antd';
import { Line } from '@ant-design/charts';

import MapItemChartSkeleton from './skeleton';

import 'antd/lib/card/style/css';
import './style.css';
import { humanizeDecimalMinutes } from '../../../../common/utils';
import { dateRangeFormatter } from '../../../../common/utils/dateRange';
import { statistics } from '../../../../common/utils/array';

const MapItemChart = ({
  data = [],
  xField = 'period',
  yField = 'value',
  isLoading = false,
  dateRange,
  title = 'Segment',
}) => {
  const { max } = statistics(data, yField);

  const pointConfig = {
    shape: 'circle',
    size: 5,
    style: {
      fill: '#BFD730',
      lineWidth: 2,
      stroke: '#BFD730',
    },
  };

  const dateRangeLength = moment(dateRange.endDate).diff(
    moment(dateRange.startDate),
    'days'
  );

  const tooltipConfig = {
    formatter: (item) => ({
      name: dateRangeFormatter(item.period, dateRangeLength),
      value: humanizeDecimalMinutes(item.value, 1),
    }),
    showMarkers: false,
    title: ' ',
  };

  const xAxisConfig = {
    label: {
      formatter: (label) => dateRangeFormatter(label, dateRangeLength),
      offset: 10,
      style: {
        fill: '#323140',
        marginTop: 28,
      },
    },
    grid: {
      line: {
        style: { stroke: '#F5F5FA' },
      },
    },
    line: {
      style: { stroke: '#F5F5FA' },
    },
    tickLine: { length: 0 },
  };

  const yAxisConfig = {
    // Force 1-second interval if max is less than 5 seconds
    // Avoids duplicate y-axis labels
    tickInterval: max < 5 / 60 && 1 / 60,
    grid: {
      line: {
        style: { stroke: '#F5F5FA' },
      },
    },
    label: {
      formatter: (label) => humanizeDecimalMinutes(label),
      style: { fill: '#323140' },
    },
    line: {
      style: { stroke: '#F5F5FA' },
    },
  };

  return isLoading ? (
    <MapItemChartSkeleton active={isLoading} />
  ) : (
    <div className="map-item-chart_container">
      <Card title={title} bordered={false}>
        <div className="map-item-chart_title">
          <div className="map-item-chart_status_top-row">
            <span>Status</span>
            {/** @todo add once tooltip text is defined */}
            {/* <InfoTooltip height={14} /> */}
          </div>
        </div>
        <Line
          data={data}
          autoFit
          interactions={[{ type: 'marker-active' }]}
          point={pointConfig}
          tooltip={tooltipConfig}
          xAxis={xAxisConfig}
          xField={xField}
          yAxis={yAxisConfig}
          yField={yField}
          color="#BFD730"
          animation={false}
          height={300}
        />
      </Card>
    </div>
  );
};

export default MapItemChart;
