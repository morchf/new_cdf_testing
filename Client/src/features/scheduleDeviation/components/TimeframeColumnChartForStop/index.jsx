import CommonChart, {
  ContentType,
  GraphType,
} from '../../../../common/components/CommonChart';
import {
  COLOR_ERROR,
  COLOR_ON_TIME,
  COLOR_EARLY,
  TODAY,
} from '../../../../common/constants';
import { useGetOnTimePercentTimeframeChartForStopsQuery } from '../../api';

const tooltipMap = {
  early: 'Early',
  onTime: 'On-Time',
  late: 'Late',
};

const createConfig = ({ data }) => ({
  // Data
  data: data.sort((a, b) => {
    const priorityArray = ['early', 'onTime', 'late'];
    const firstPrio = priorityArray.indexOf(a.status);
    const secPrio = priorityArray.indexOf(b.status);
    return firstPrio - secPrio;
  }),
  yField: 'value',
  seriesField: 'status',

  // Axes
  yAxisTitle: '%',

  // Extra
  tooltip: {
    showTitle: false,
    formatter: (ref) => {
      const { value, status } = ref;
      return {
        name: `${tooltipMap[status]} Percentage`,
        value: `${(value * 100).toFixed(1)} %`,
      };
    },
  },

  // Styling
  color: ({ status }) => {
    if (status === 'early') {
      return COLOR_EARLY;
    }
    if (status === 'onTime') {
      return COLOR_ON_TIME;
    }
    return COLOR_ERROR;
  },
  stroke: '#fb8658',
  legend: false,
  columnWidthRatio: 0.97,
  isPercent: true,
  annotationStroke: '#333333',
});

const TimeframeColumnChartForStop = ({ dateRange }) => {
  const { data: timeframeChart, isFetching: isTimeframeChartLoading } =
    useGetOnTimePercentTimeframeChartForStopsQuery();

  return (
    <>
      <CommonChart
        metric="onTimePercentage"
        today={TODAY}
        graphType={GraphType.Column}
        contentType={ContentType.Time}
        data={timeframeChart}
        loading={isTimeframeChartLoading}
        dateRange={dateRange}
        style={{ height: 430 }}
        createConfig={createConfig}
      />
    </>
  );
};

export default TimeframeColumnChartForStop;
