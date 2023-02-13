import React, { useCallback } from 'react';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import TableCard from '../../../../common/components/TableCard';
import CommonChart, {
  ContentType,
  GraphType,
} from '../../../../common/components/CommonChart';
import {
  metricColorMap,
  metricsNames,
  TODAY,
} from '../../../../common/constants';
import useMetricChart from '../../hooks/useMetricChart';
import './style.css';
import { lineChartPath } from '../../../../common/components/CommonChart/shapes';

const createChartConfig =
  ({ metric }) =>
  ({ data }) => ({
    data: data.map(({ value, ...rest }) => ({
      value: +value,
      series: metric,
      ...rest,
    })),
    xField: 'period',
    yField: 'value',
    stroke: metricColorMap[metric],
    annotationStroke: '#333333',

    // Legend
    legendItems: [
      {
        field: metric,
        label: `${metricsNames[metric]}s`,
        symbol: lineChartPath,
        stroke: metricColorMap[metric],
      },
    ],
    seriesField: 'series',
  });

const AverageMetricsChart = ({ match, metric, dateRange }) => {
  const { route: routeName } = match.params;
  const { chart, isLoading } = useMetricChart({ routeName, metric });

  const createConfig = useCallback(
    (...rest) => createChartConfig({ metric })(...rest),
    [metric]
  );

  const isEmpty = !isLoading && !chart?.length;

  return isEmpty ? (
    <></>
  ) : (
    <TableCard>
      <CommonChart
        metric={metric}
        today={TODAY}
        graphType={GraphType.Line}
        contentType={ContentType.Time}
        data={chart}
        loading={isLoading}
        routeName={routeName}
        dateRange={dateRange}
        createConfig={createConfig}
        removeFrequency
      />
    </TableCard>
  );
};
const mapStateToProps = ({ routeFilters }) => {
  const { dateRange } = routeFilters;
  return { dateRange };
};

export default connect(mapStateToProps)(withRouter(AverageMetricsChart));
