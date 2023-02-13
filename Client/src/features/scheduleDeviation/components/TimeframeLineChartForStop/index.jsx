import CommonChart, {
  ContentType,
  GraphType,
} from '../../../../common/components/CommonChart';
import { TODAY } from '../../../../common/constants';
import { useGetDeviationTimeframeChartForStopsQuery } from '../../api';

const createConfig = ({ data }) => ({
  data: data.map(({ lateness, ...rest }) => ({ lateness: +lateness, ...rest })),
  yField: 'lateness',
  padding: [25, 25, 75, 75],
  stroke: '#3911bc',
  annotationStroke: '#333333',
});

const TimeframeLineChartForStop = ({ dateRange }) => {
  const { data: timeframeChart, isFetching: isTimeframeChartLoading } =
    useGetDeviationTimeframeChartForStopsQuery();

  return (
    <>
      <CommonChart
        metric="scheduleDeviation"
        today={TODAY}
        graphType={GraphType.Line}
        contentType={ContentType.Time}
        data={timeframeChart}
        loading={isTimeframeChartLoading}
        dateRange={dateRange}
        style={{ height: 482 }}
        createConfig={createConfig}
      />
    </>
  );
};

export default TimeframeLineChartForStop;
