import { useMemo } from 'react';
import { Column, Line } from '@ant-design/charts';
import { Typography as AntTypography } from 'antd';
import { Period } from '../../enums';
import { getXAxisLabel, getXAxisFormatter, isWeekend } from './utils';
import { TIME_LABEL_MAP } from '../../utils/dateRange';
import Skeleton from '../Skeleton';
import useChartResize from './hooks/useChartResize';
import { metricsNames } from '../../constants';
import { humanizeDecimalMinutes } from '../../utils';
import {
  createUnusedZones,
  dottedLinePath,
  squarePath,
  transformLegendItems,
} from './shapes';
import useCustomChart from './hooks/useCustomChart';
import { statistics } from '../../utils/array';
import './style.css';

const { Title: AntTitle } = AntTypography;

export const ContentType = {
  Stop: 'Stop',
  Time: 'Time',
};
export const GraphType = {
  Column: 'Column',
  Line: 'Line',
};

const createDefaultConfig = ({
  data,
  metric,
  isStop,
  graphType,
  yAxisTitle,
  yField: existingYField,
  xField: existingXField,
  xAxisLabel,
  xAxisFormatter,
  stroke,
  annotationStroke,
  legendItems,
  seriesField,
  meanSeries,
  isPercent,
  meanSeriesFormatter = (value) => value,
}) => {
  const xField = existingXField || (isStop ? 'stopNumber' : 'time');
  const yField = existingYField || 'lateness';
  const meanLabel = isStop ? 'Stop' : 'Day';

  // Absolute max value is less than a minute
  const isSeconds =
    !isPercent &&
    data.reduce((max, item) => {
      const value = Math.abs(item[yField]);
      return value > max ? value : max;
    }, 0) <= 1;

  const scaledData = isSeconds
    ? data.map((item) => ({ ...item, [yField]: item[yField] * 60 }))
    : data;
  const { max } = statistics(scaledData, yField);

  // Annotations
  let annotations = [];
  if (data?.length) {
    // Add grayed-out area for null values
    const emptyAnnotations = createUnusedZones(data, yField);
    if (emptyAnnotations?.length) {
      legendItems.push({
        field: 'empty',
        label: 'No Data',
        symbol: squarePath,
        fill: 'rgba(0, 0, 0, 0.08)',
      });
    }

    // Calculate the mean line from a single series, if enabled
    let meanYValue = 'mean';
    if (meanSeries) {
      const meanSeriesData = data.filter(
        (item) =>
          item[seriesField] === meanSeries && !Number.isNaN(item[yField])
      );
      const meanSeriesSum = meanSeriesData.reduce(
        (sum, item) => sum + item[yField],
        0
      );
      meanYValue = meanSeriesSum / meanSeriesData.length;
    }

    annotations = [
      // Mean line
      {
        type: 'line',
        start: [-0.5, meanYValue],
        end: [data.length - 0.5, meanYValue],
        style: {
          stroke: annotationStroke,
          lineWidth: 1.5,
          lineDash: [10, 7],
        },
      },
      // Mean Line Label
      {
        type: 'text',
        position: ['max', meanYValue],
        content: `Avg by ${meanLabel}`,
        offsetY: 4,
        offsetX: -60,
        style: {
          textBaseline: 'top',
        },
      },
      ...emptyAnnotations,
    ];
  }

  // Legend
  const metricName = metricsNames[metric];
  const annotationLabel = `Avg ${metricName} by ${meanLabel}`;
  const legendItemsWithMean = legendItems
    ? [
        ...transformLegendItems(legendItems),
        {
          id: 'mean',
          value: 'mean',
          name: 'mean',
          label: annotationLabel,
          marker: {
            symbol: () => dottedLinePath,
            style: {
              stroke: annotationStroke,
              fill: '',
              lineWidth: 2,
            },
            spacing: 35,
          },
        },
      ]
    : [];

  return {
    // Data
    data: scaledData,
    xField,
    yField,
    connectNulls: false,
    isPercent: false,

    // Axes
    xAxisLabel,
    xAxis: {
      title: {
        offset: 55,
        position: 'start',
        style: {
          fontWeight: 450,
          fill: 'black',
          height: 250,
          lineHeight: 200,
          textAlign: 'left',
        },
        text: xAxisLabel,
      },
      label: {
        offset: 15,
        formatter: xAxisFormatter,
        style: (text, index, array) => {
          const { name: date } = array[index];

          // Color weekend labels
          return {
            fill: !isStop && isWeekend(date) ? '#4382FF' : '#999999',
            textBaseLine: 'bottom',
            fontWeight: 450,
            textAlign: 'center',
          };
        },
      },
      tickLine: null,
    },
    isStack: isPercent,
    yAxis: {
      tickInterval: !isPercent && max < 5 ? 1 : null,
      label: {
        style: {
          fontWeight: 450,
          fill: '#999999',
        },
        formatter: isPercent
          ? (value) => value * 100
          : (value) => (+value).toFixed(isSeconds ? 1 : 0),
      },
      max: isPercent && 1,
      title: {
        style: {
          fontWeight: 450,
          fill: 'black',
        },
        text: `${yAxisTitle || (isSeconds ? 'SEC' : 'MIN')}\n\n\n`, // Position text vertically
        position: 'end',
        offset: 0,
        rotate: 0,
      },
    },

    // Extras
    tooltip: {
      showTitle: isStop,
      title: (text, ref) => (!isStop ? text : ref.stopname),
      formatter: (ref) => {
        const name = ref[xField];
        const rawValue = isSeconds ? ref[yField] / 60 : ref[yField];

        const value = Number.isNaN(rawValue)
          ? 'No Data'
          : humanizeDecimalMinutes(rawValue, Math.abs(rawValue) < 1 ? 1 : 0);
        return { name, value };
      },
    },
    point: !isStop && {
      size: 3,
      shape: 'circle',
    },
    legend: {
      position: 'bottom',
      items: legendItemsWithMean,
      maxItemWidth: 350,
      itemName: {
        formatter: (key, { label }) => label || key,
      },
    },
    seriesField,

    // Styling
    color: stroke,
    animation: false,
    annotations,
    padding: [30, 0, 90, 35],
  };
};

/* Create labels of the format 01 ... 10 ... */
const addStopNumbers = (isStop, data) => {
  if (!isStop) return data;

  // Maps existing stops for aggregate data
  const stopNumberMap = new Map();
  let currStopNumber = 1;
  return data.map(({ stopname, ...rest }) => {
    let stopNumber;
    if (stopNumberMap.has(stopname)) {
      stopNumber = stopNumberMap.get(stopname);
    } else {
      stopNumber = `${currStopNumber}`.padStart(2, '0');
      currStopNumber += 1;
      stopNumberMap.set(stopname, stopNumber);
    }

    return {
      stopname,
      ...rest,
      stopNumber,
    };
  });
};

const mergeConfigs = ({
  data,
  metric,
  isStop,
  graphType,
  xAxisLabel,
  xAxisFormatter,
  createConfig,
}) => {
  // Add stop number labels for stop graph
  const mappedData = addStopNumbers(isStop, data);

  // Create config
  const {
    annotations,
    data: configData,
    xField,
    yField,
    padding,
    ...rest
  } = createConfig({
    data: mappedData,
    isStop,
  });

  // Create default config with passed-in overrides
  const {
    annotations: defaultAnnotations,
    padding: defaultPadding,
    ...defaultRest
  } = createDefaultConfig({
    data: configData,
    metric,
    isStop,
    graphType,
    xField,
    yField,
    xAxisLabel,
    xAxisFormatter,
    ...rest,
  });

  // Merge both padding
  const mergedPadding = [];
  for (let i = 0; i < 4; i += 1) {
    mergedPadding[i] =
      padding && padding[i] != null ? padding[i] : defaultPadding[i];
  }

  // Merge default and passed-in configs
  return {
    ...defaultRest,
    annotations: [...(annotations || []), ...defaultAnnotations],
    ...rest,
    padding: mergedPadding,

    // Override default percent handling
    isPercent: false,
  };
};

const Header = ({ frequency, metricName, color, routeName = null }) => (
  <AntTitle level={3}>
    <span style={{ color }}>{metricName}</span>
    <span style={{ fontWeight: 720 }}>{frequency && ` by ${frequency} `}</span>
    {routeName && ` ${frequency ? 'on' : 'for'} Route ${routeName}`}
  </AntTitle>
);

const CommonChart = ({
  today,
  metric,
  graphType,
  contentType,
  data,
  loading,
  routeName,
  createConfig,
  tools,
  dateRange,
  frequency = Period.Day,
  removeFrequency = false,
  ...props
}) => {
  const isStop = useMemo(() => contentType === ContentType.Stop, [contentType]);

  // Header labels from filters
  const frequencyLabel = useMemo(
    () => !removeFrequency && (isStop ? 'Stop' : TIME_LABEL_MAP[frequency]),
    [isStop, removeFrequency, frequency]
  );

  const { annotations, xField, ...config } = useMemo(() => {
    // Chart configuration from filters
    const xAxisFormatter = getXAxisFormatter(isStop, frequency);
    const xAxisLabel = isStop ? 'Stop' : getXAxisLabel({ dateRange });

    return mergeConfigs({
      data: data?.length ? data.slice() : [],
      metric,
      isStop,
      graphType,
      xAxisLabel,
      xAxisFormatter,
      createConfig,
    });
  }, [isStop, frequency, dateRange, data, metric, graphType, createConfig]);

  const chart = useChartResize();
  const { onReady } = useCustomChart();

  return (
    <section className="common-chart">
      {!loading ? (
        <>
          {tools && <div className="common-chart__tools">{tools}</div>}
          <Header
            routeName={routeName}
            frequency={frequencyLabel}
            metricName={metricsNames[metric]}
            color={config.stroke || config.color}
          />
          {graphType === GraphType.Column && (
            <Column
              autoFit
              annotations={annotations}
              xField={xField}
              {...config}
              {...props}
              ref={chart}
              onReady={onReady}
            />
          )}
          {graphType === GraphType.Line && (
            <Line
              autoFit
              annotations={annotations}
              xField={xField}
              {...config}
              {...props}
              ref={chart}
              onReady={onReady}
            />
          )}
        </>
      ) : (
        <Skeleton style={{ height: 450 }} {...props} />
      )}
    </section>
  );
};

CommonChart.Header = Header;
export { Header };
export default CommonChart;
