import React, { memo } from 'react';
import { Bar } from '@ant-design/charts';
import { Divider } from 'antd';
import './style.css';
import {
  COLOR_ERROR,
  COLOR_NORMAL,
  COLOR_WARNING,
} from '../../../../common/constants';

const StatusHistogram = ({ data }) => {
  const config = {
    data,
    xField: 'count',
    yField: 'type',
    seriesField: 'type',
    color: function color(_ref) {
      const { type } = _ref;
      if (type === 'Normal') {
        return COLOR_NORMAL;
      }
      if (type === 'Error') {
        return COLOR_ERROR;
      }
      return COLOR_WARNING;
    },
    yAxis: {
      label: {
        style: {
          fontWeight: 450,
          fill: 'black',
        },
      },
    },
    legend: false,
    barWidthRatio: 0.2,
    barStyle: {
      radius: [20, 20, 0, 0],
    },
    label: {
      position: 'right',
      offset: 20,
      content: function content(_ref) {
        const { count } = _ref;
        return count;
      },
      style: {
        fontWeight: 450,
        fill: 'black',
      },
    },
    padding: [20, 60, 200, 80],
  };

  return (
    <div className="status-histogram-container">
      <div className="status-histogram-text">
        <h4>Current Status</h4>
      </div>
      <Divider />
      <Bar {...config} />;
    </div>
  );
};

export default memo(StatusHistogram);
