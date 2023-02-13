import React, { Children } from 'react';
import { Empty, Radio } from 'antd';
import AverageMetricsItem, {
  createTransitDelayLabels,
  createScheduleDeviationLabels,
} from './AverageMetricsItem';

import './style.css';
import Skeleton from '../Skeleton';

const Tab = ({ metric, hasLowConfidenceData, ...props }) => (
  <AverageMetricsItem
    metric={metric}
    hasLowConfidenceData={hasLowConfidenceData}
    {...props}
  />
);

const Tabs = ({ avgMetrics, dateRange, children, ...props }) =>
  Children.map(children, (child) => {
    if (!child.props) return child;

    const { metric } = child.props;
    if (!metric) return child;
    const item = avgMetrics[metric];

    return (
      item &&
      React.cloneElement(child, {
        metric,
        item,
        dateRange,
        ...props,
      })
    );
  });

const AverageMetrics = ({
  selectedMetric,
  onSelectedMetricChange,
  isLoading,
  dateRange,
  avgMetrics = {},
  numMetrics = 4,
  children,
  ...props
}) => {
  const isEmpty = !Object.keys(avgMetrics).length;

  return (
    <div>
      {!isLoading && isEmpty ? (
        <div className="avg-empty-container">
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </div>
      ) : (
        <Radio.Group
          className={`avg-metrics-container ${
            isLoading ? 'avg-metrics-container--loading' : ''
          } ${
            // Items require spacing to column format on smaller screens
            numMetrics > 2 ? 'avg-metrics-container--large' : ''
          }
          ${
            // Grid template must update for spacers
            children?.length !== numMetrics
              ? 'avg-metrics-container--spacers'
              : ''
          }`}
          value={selectedMetric}
          onChange={(event) => onSelectedMetricChange(event.target.value)}
          {...props}
        >
          {isLoading && (
            <Skeleton
              number={numMetrics}
              className="avg-metrics__skeleton"
              active={isLoading}
            />
          )}
          {!isLoading && !isEmpty && (
            <Tabs avgMetrics={avgMetrics} dateRange={dateRange}>
              {children}
            </Tabs>
          )}
        </Radio.Group>
      )}
    </div>
  );
};

AverageMetrics.Tab = Tab;
export default AverageMetrics;
export { createScheduleDeviationLabels, createTransitDelayLabels };
