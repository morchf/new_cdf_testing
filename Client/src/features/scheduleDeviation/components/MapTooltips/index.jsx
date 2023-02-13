import React from 'react';
import { Card } from 'antd';

import 'antd/lib/card/style/css';
import './style.css';
import {
  capitalize1stLetter,
  convertRelativeToPercentages,
  humanizeDeviationLabel,
} from '../../../../common/utils';
import RelativeLink from '../../../../common/components/RelativeLink';
import { metricsNames } from '../../../../common/constants';
import { Metric } from '../../../../common/enums';

const Title = ({ title, isLink }) => {
  if (!isLink) {
    return title;
  }
  return <RelativeLink to={title}>{title}</RelativeLink>;
};

const Labels = ({ item, metric }) => {
  if (metric === Metric.OnTimePercentage) {
    const onTimePercentage = item?.ontimepercentage?.percent;
    const earlyPercentage = item?.earlypercentage?.percent;
    const latePercentage = item?.latepercentage?.percent;

    if (
      onTimePercentage == null &&
      earlyPercentage == null &&
      latePercentage == null
    ) {
      return <div>No Data</div>;
    }

    const [onTimePer, earlyPerc, latePerc] = convertRelativeToPercentages(
      [onTimePercentage, earlyPercentage, latePercentage],
      1
    );

    return (
      <>
        <div>
          <b>Late Percentage: </b>
          <span>{latePerc}</span>
        </div>
        <div>
          <b>On-time Percentage: </b>
          <span>{onTimePer}</span>
        </div>
        <div>
          <b>Early Percentage: </b>
          <span>{earlyPerc}</span>
        </div>
      </>
    );
  }

  const value = item?.lateness
    ? humanizeDeviationLabel(item?.lateness)
    : 'Not available';

  return (
    <div>
      <b>{metricsNames[metric]}: </b>
      <span>{value}</span>
    </div>
  );
};

const LatenessPointTooltip = ({ item, metric, isLink = false }) => (
  <Card
    className="lateness-tooltip"
    size="small"
    title={<Title title={item?.stopNameShort} isLink={isLink} />}
    style={{ width: 250 }}
  >
    <div>
      <b>Route: </b>
      <span>{item?.route}</span>
    </div>
    {item?.direction && (
      <div>
        <b>Direction: </b>
        <span>{capitalize1stLetter(item?.direction)}</span>
      </div>
    )}
    <div>
      <b>Stop Number: </b>
      <span>{item?.stopNumber}</span>
    </div>
    <Labels item={item} metric={metric} />
  </Card>
);

const BusStopTooltip = ({ olFeature }) => (
  <Card size="small" title="Bus Stop" style={{ width: 250 }}>
    {olFeature.get('stopname')}
  </Card>
);

const StartTooltip = ({ olFeature }) => (
  <Card size="small" title="Route Start" style={{ width: 250 }}>
    {olFeature.get('stopname')}
  </Card>
);

const EndTooltip = ({ olFeature }) => (
  <Card size="small" title="Route End" style={{ width: 250 }}>
    {olFeature.get('stopname')}
  </Card>
);

export { LatenessPointTooltip, BusStopTooltip, StartTooltip, EndTooltip };
