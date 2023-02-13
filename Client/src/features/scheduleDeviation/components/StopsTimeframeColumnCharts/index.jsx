import { useEffect, useMemo, useState } from 'react';
import {
  COLOR_EARLY,
  COLOR_ERROR,
  COLOR_ON_TIME,
  TODAY,
} from '../../../../common/constants';
import CommonChart, {
  GraphType,
  ContentType,
} from '../../../../common/components/CommonChart';
import { squarePath } from '../../../../common/components/CommonChart/shapes';
import TableCard from '../../../../common/components/TableCard';
import { Direction, Metric } from '../../../../common/enums';
import { transformColumnChartData } from '../../utils';
import useTimeframe from '../../hooks/useTimeframe';
import useMap from '../../hooks/useMap';
import MiniRadio from '../../../../common/components/MiniRadio';
import { capitalize1stLetter } from '../../../../common/utils';

const tooltipMap = {
  early: 'Early',
  onTime: 'On-Time',
  late: 'Late',
};

const createConfig = ({ data, isStop }) => ({
  // Data
  data: data
    .sort((a, b) => {
      const priorityArray = ['early', 'onTime', 'late'];
      const firstPrio = priorityArray.indexOf(a.status);
      const secPrio = priorityArray.indexOf(b.status);
      return firstPrio - secPrio;
    })
    .map(({ value, ...rest }) => ({ ...rest, value: value / 100 })),
  yField: 'value',
  xField: !isStop && 'period',
  seriesField: 'status',
  meanSeries: 'onTime', // Series determining mean line

  // Axes
  yAxisTitle: '%',

  // Extras
  tooltip: {
    showTitle: true,
    title: (text, ref) => (!isStop ? text : ref.stopname),
    formatter: (ref, ...rest) => {
      const { value, status } = ref;
      const name = `${tooltipMap[status]} Percentage`;

      if (Number.isNaN(+value)) {
        return { name, value: 'No Data' };
      }

      return {
        name,
        value: `${(value * 100).toFixed(1)} %`,
      };
    },
  },

  // Styling
  columnWidthRatio: 0.97,
  isPercent: true,
  annotationStroke: '#333333',
  stroke: '#fb8658',
  color: ({ status }) => {
    if (status === 'early') {
      return COLOR_EARLY;
    }
    if (status === 'onTime') {
      return COLOR_ON_TIME;
    }
    return COLOR_ERROR;
  },

  // Legend
  legendItems: [
    {
      field: 'late',
      label: tooltipMap.late,
      symbol: squarePath,
      fill: COLOR_ERROR,
    },
    {
      field: 'onTime',
      label: tooltipMap.onTime,
      symbol: squarePath,
      fill: COLOR_ON_TIME,
    },
    {
      field: 'early',
      label: tooltipMap.early,
      symbol: squarePath,
      fill: COLOR_EARLY,
    },
  ],
});

const StopsTimeframeColumnCharts = ({ routeName, dateRange, direction }) => {
  const { stops, isLoading: isStopsChartLoading } = useMap({
    routeName,
  });

  const { timeframe, isLoading: isTimeframeChartLoading } = useTimeframe({
    routeName,
  });

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

  const { stopsChart, timeframeChart } = useMemo(
    () => ({
      stopsChart: transformColumnChartData(
        directions && selectedDirection
          ? stops.filter(({ direction: d }) => d === selectedDirection)
          : stops,
        false
      ),
      timeframeChart: transformColumnChartData(timeframe, true),
    }),
    [directions, selectedDirection, stops, timeframe]
  );

  return (
    <>
      {(isTimeframeChartLoading || !!timeframeChart?.length) && (
        <TableCard>
          <CommonChart
            metric="onTimePercentage"
            today={TODAY}
            graphType={GraphType.Column}
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
            metric={Metric.OnTimePercentage}
            today={TODAY}
            graphType={GraphType.Column}
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

export default StopsTimeframeColumnCharts;
