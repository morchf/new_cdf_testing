import React, { memo } from 'react';
import { Bar } from '@ant-design/charts';
import { Divider } from 'antd';
import './style.css';

const compareVersions = (v1, v2) => {
  const digits1 = v1.split('.');
  const digits2 = v2.split('.');
  for (let i = 0; i < Math.max(digits1.length, digits2.length); i++) {
    const d1 = parseInt(digits1[i], 10) || 0;
    const d2 = parseInt(digits2[i], 10) || 0;
    if (d1 > d2) {
      return v1;
    }
    if (d1 < d2) {
      return v2;
    }
  }
  return v1; // default if v1 and v2 have the same value
};
const findLatestVersion = (versions) => {
  let latest = versions[0];
  for (let i = 1; i < versions.length; i++) {
    latest = compareVersions(latest, versions[i]);
  }
  return latest;
};

const FirmwareHistogram = ({ data }) => {
  const versionsCount = data.reduce((vc, intersection) => {
    vc[intersection.version] = (vc[intersection.version] || 0) + 1;
    return vc;
  }, {});
  const latestVersion = findLatestVersion(Object.keys(versionsCount));
  const versionsForHist = [
    {
      type: 'Up-to-date',
      count: 0,
    },
    {
      type: 'Not Up-to-date',
      count: 0,
    },
  ];
  Object.entries(versionsCount).forEach(([version, count]) => {
    if (version === latestVersion) {
      versionsForHist[0].count += count;
    } else {
      versionsForHist[1].count += count;
    }
  });

  const config = {
    data: versionsForHist,
    xField: 'count',
    yField: 'type',
    seriesField: 'type',
    color: function color(_ref) {
      const { type } = _ref;
      if (type === 'Up-to-date') {
        return '#BFD730';
      }
      return '#EEBA00';
    },
    yAxis: {
      label: {
        style: {
          fontWeight: 450,
          fill: 'black',
          align: 'left',
        },
        offset: 30,
        formatter: (text) => {
          if (text === 'Up-to-date') {
            return 'Base Selector that match Up to\nDate Firmware Version';
          }
          return 'Base Selector that does not match Up\nto Date Firmware Version';
        },
      },
    },
    legend: false,
    barWidthRatio: 0.13,
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
    padding: [20, 70, 200, 270],
  };

  return (
    <div className="firmware-histogram-container">
      <div className="firmware-histogram-text">
        <h4>Firmware</h4>
      </div>
      <Divider />
      <Bar {...config} />;
    </div>
  );
};

export default memo(FirmwareHistogram);
