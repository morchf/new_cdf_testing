import React from 'react';
import { Radio } from 'antd';
import {
  convertRelativeToPercentages,
  humanizeDecimalMinutes,
  humanizeDeviationLabel,
} from '../../../utils';
import { COLOR_ERROR, COLOR_POSITIVE, metricsNames } from '../../../constants';
import TrendLineIcon from '../../../icons/TrendLine';
import InfoTooltip from '../../InfoTooltip';
import { Metric } from '../../../enums';
import './style.css';

const TrendIcon = ({ isBetter }) => (
  <TrendLineIcon
    className="avg-metrics_item-icon"
    style={{
      color: !isBetter ? COLOR_ERROR : COLOR_POSITIVE,
      transform: !isBetter ? 'scale(1, -1)' : '',
    }}
  />
);

const getDeltaString = (change, isBetter) => {
  if (change == null) return null;

  // response value is in seconds. convert to minutes for TSD metrics.
  const deltaSec = Math.abs(Math.round(change));
  const comparison = isBetter ? 'better' : 'worse';

  return `${humanizeDecimalMinutes(
    deltaSec / 60
  )} ${comparison} than the last period`;
};

export const createTransitDelayLabels =
  ({ totalMins }) =>
  (item, metric) => {
    const { change, isBetter, mins } = item;

    const label2 = getDeltaString(change, isBetter);

    // Handle missing values. Substitute invalid metrics for 0
    const value = mins == null ? 0 : humanizeDecimalMinutes(mins);
    const label1 = `${
      mins == null || totalMins == null
        ? 0
        : Math.round((100 * mins) / totalMins)
    }% of Route Time`;
    const valueWithIcon = (
      <>
        {value}
        {metric === Metric.TravelTime && <TrendIcon isBetter={isBetter} />}
      </>
    );

    return {
      value: valueWithIcon,
      label1,
      label2,
    };
  };

const percentageMetrics = ['onTimePercentage'];
const deviationMetrics = ['scheduleDeviation'];

export const createScheduleDeviationLabels = () => (item, metric) => {
  const { isBetter, change, mins } = item;

  const label2 = getDeltaString(change, isBetter);

  // Main value and any additional label
  let label3;
  let label4;
  let value;
  if (percentageMetrics.includes(metric)) {
    const { onTimeRate, earlyRate, lateRate } = item;
    const [onTimePer, earlyPerc, latePerc] = convertRelativeToPercentages([
      onTimeRate,
      earlyRate,
      lateRate,
    ]);
    label3 = `Early ${earlyPerc} - Late ${latePerc}`;
    value = onTimePer;
  }

  if (deviationMetrics.includes(metric)) {
    const fullLabel = humanizeDeviationLabel(mins);
    const cardLabel = fullLabel.split(' ');

    // remove ahead/behind into separate label and rejoin string
    label4 = cardLabel.pop();
    value = cardLabel.join(' ');
  }

  return { value, label2, label3, label4 };
};

const isAverage = ['signaldelay', 'dwelltime', 'drivetime', 'traveltime'];

const AverageMetricsItem = ({
  metric,
  item,
  hasLowConfidenceData,
  createLabels,
  tooltip,
  className = '',
  ...props
}) => {
  // Caption beneath large block
  const title = isAverage.includes(metric)
    ? `${metricsNames[metric]} (avg)`
    : `${metricsNames[metric]}`;
  const { isBetter } = item;
  const { value, label1, label2, label3, label4 } = createLabels(item, metric);

  return (
    <>
      {value && title && (
        <Radio.Button
          value={metric}
          key={metric}
          className={`avg-metrics-item ${className}`}
          {...props}
        >
          <div className="avg-metrics_item-info">
            {tooltip && (
              <InfoTooltip text={tooltip} danger={hasLowConfidenceData} />
            )}
          </div>
          <div className="avg-metrics_item-content">
            <div className="avg-metrics_item-header">
              {value}
              {label4 && (
                <div className="avg-metrics_item-label4">({label4})</div>
              )}
            </div>
            <div className="avg-metrics_item-content_left">
              {label1 && (
                <div className="avg-metrics_item-label1">{label1}</div>
              )}
              {label2 && (
                <div
                  className={`avg-metrics_item-label2 ${
                    isBetter != null && isBetter
                      ? 'avg-metrics_item-label2--better'
                      : ''
                  } ${
                    isBetter != null && !isBetter
                      ? 'avg-metrics_item-label2--worse'
                      : ''
                  }`}
                >
                  {label2}
                </div>
              )}
              {label3 && (
                <div className="avg-metrics_item-label3">{label3}</div>
              )}
            </div>

            <div className="avg-metrics_item-name">{title}</div>
          </div>
        </Radio.Button>
      )}
    </>
  );
};

export default AverageMetricsItem;
