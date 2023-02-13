import { useEffect, useMemo, useState } from 'react';
import { connect } from 'react-redux';
import {
  metricColorMap,
  TODAY,
  metricsNames,
} from '../../../../common/constants';
import CommonChart, {
  GraphType,
  ContentType,
} from '../../../../common/components/CommonChart';
import TableCard from '../../../../common/components/TableCard';
import { lineChartPath } from '../../../../common/components/CommonChart/shapes';
import { Direction, Metric } from '../../../../common/enums';
import useTimeframe from '../../hooks/useTimeframe';
import useMap from '../../hooks/useMap';
import MiniRadio from '../../../../common/components/MiniRadio';
import { capitalize1stLetter } from '../../../../common/utils';

const createConfig = ({ data, isStop }) => ({
  // Data
  data: data.map(({ lateness, ...rest }) => ({
    lateness: +lateness,
    series: Metric.ScheduleDeviation,
    ...rest,
  })),
  xField: !isStop && 'period',
  yField: 'lateness',

  // Styling
  stepType: isStop && 'hvh',
  stroke: metricColorMap.scheduleDeviation,
  annotationStroke: '#333333',

  // Legend
  legendItems: [
    {
      field: Metric.ScheduleDeviation,
      label: `${metricsNames.scheduleDeviation}s`,
      symbol: lineChartPath,
      stroke: metricColorMap.scheduleDeviation,
    },
  ],
  seriesField: 'series',
});

const StopsTimeframeLineCharts = ({ routeName, dateRange, direction }) => {
  // Direction
  const directions = useMemo(
    () =>
      direction === Direction.All
        ? [Direction.Inbound, Direction.Outbound]
        : null,

    [direction]
  );
  const [selectedDirection, setSelectedDirection] = useState();
  useEffect(() => {
    if (direction === Direction.All && !selectedDirection) {
      setSelectedDirection(Direction.Inbound);
    }
  }, [direction, selectedDirection]);

  const { timeframe: timeframeChart, isLoading: isTimeframeChartLoading } =
    useTimeframe({
      routeName,
    });
  const { stops, isLoading: isStopsChartLoading } = useMap({
    routeName,
  });

  const stopsChart = useMemo(
    () =>
      directions && selectedDirection
        ? stops.filter(({ direction: d }) => d === selectedDirection)
        : stops,
    [directions, selectedDirection, stops]
  );

  return (
    <>
      {(isTimeframeChartLoading || !!timeframeChart?.length) && (
        <TableCard>
          <CommonChart
            metric="scheduleDeviation"
            today={TODAY}
            graphType={GraphType.Line}
            contentType={ContentType.Time}
            data={timeframeChart}
            loading={isTimeframeChartLoading}
            routeName={routeName}
            dateRange={dateRange}
            style={{ height: 430 }}
            createConfig={createConfig}
          />
        </TableCard>
      )}
      {(isStopsChartLoading || !!stopsChart?.length) && (
        <TableCard>
          <CommonChart
            metric="scheduleDeviation"
            today={TODAY}
            graphType={GraphType.Line}
            contentType={ContentType.Stop}
            data={stopsChart}
            loading={isStopsChartLoading}
            routeName={routeName}
            dateRange={dateRange}
            style={{ height: 482 }}
            createConfig={createConfig}
            tools={
              <>
                {directions && (
                  <MiniRadio.Group
                    value={selectedDirection}
                    onChange={(e) => setSelectedDirection(e.target.value)}
                  >
                    {directions.map((d) => (
                      <MiniRadio.Button value={d} key={d}>
                        {capitalize1stLetter(d)}
                      </MiniRadio.Button>
                    ))}
                  </MiniRadio.Group>
                )}
              </>
            }
          />
        </TableCard>
      )}
    </>
  );
};

const mapStateToProps = ({ routeFilters }) => routeFilters;

export default connect(mapStateToProps)(StopsTimeframeLineCharts);
