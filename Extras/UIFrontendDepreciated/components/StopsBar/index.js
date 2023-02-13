import { Line } from '@ant-design/charts';
import { useCallback, useEffect, useRef } from 'react';
import { maxLengthFormatter } from '../../utils';
import Skeleton from '../../../Skeleton';
import { createStopsLine, createStopTick } from '../../shapes';
import './style.css';

const SEGMENT_WIDTH = 100;
const HEIGHT_TO_WIDTH_RATIO = 0.25;

/* Clamp chart width to container width */
const calculateWidth = (width, container) => {
  if (container?.current && container.current.clientWidth > width) {
    return container.current.clientWidth;
  }

  return width;
};

/* Find the unique number of occurrences of the field data */
const calculateNumOccurrences = (data, field) =>
  data.reduce((acc, item) => acc.add(item[field]), new Set()).size;

const StopsBar = ({
  data,
  isLoading,
  stroke,
  xField: defaultXField,
  yField,
  seriesField = 'series',
  annotations = [],
  addTabs = false,
  ...props
}) => {
  const container = useRef();
  const chart = useRef();

  const xField = defaultXField || 'stopname';

  // Add line for stops
  const stopAnnotations = [createStopsLine(stroke)];
  const spacedData = [
    // Filter to a single series
    ...data.reduce(
      ({ singleSeries, seriesId }, current) => {
        const selectedSeries = seriesId || current[seriesField];

        if (current[seriesField] === selectedSeries) {
          singleSeries.push(current);
        }

        return { singleSeries, seriesId: selectedSeries };
      },
      { seriesId: undefined, singleSeries: [] }
    ).singleSeries,
  ].map((item, index) => {
    // Add tick for each stop
    stopAnnotations.push(createStopTick(index, 'black'));

    // Create fake y-point for spacing
    return {
      ...item,
      // Need to keep duplicate stop names from breaking spacing
      [xField]: `${item[xField]} (${index + 1})`,
      '--spacing': 1,
    };
  });

  const styles = {};
  if (props?.padding?.length) {
    // Allow parent to change left/right padding
    styles.marginLeft = props.padding[3] - 25;
    styles.marginRight = props.padding[1] - 25;
  }

  const config = {
    // Data
    data: spacedData.map(({ stopname, ...rest }, index) => ({
      stopname: `${stopname}\n${(index + 1).toString().padStart(2, '0')}`,
      ...rest,
    })),
    xField,
    yField: '--spacing',

    // Axes
    yAxis: false,
    xAxis: {
      label: {
        rotate: -0.56, // Radians
        offset: -20,
        formatter: (text) => {
          const [label, stopNumber] = text.split('\n');
          return `Stop ${stopNumber}\n${maxLengthFormatter(label)}`;
        },
        style: {
          fill: `l(90) 0:${stroke} 0.45:${stroke} 0.50:#000000 1:#000000`,
          textBaseLine: 'bottom',
          fontWeight: 450,
          textAlign: 'left',
        },
      },
      // Remove x-axis line
      line: {
        style: {
          stroke: 'transparent',
        },
      },
    },

    // Styling
    color: 'transparent',
    stepType: 'hvh',
    tooltip: false,
    padding: [25, 50, 50, 25],
    annotations: [...stopAnnotations, ...(annotations || [])],
    animation: false,
    isStack: false,
    legend: false,
  };

  // Calculate the number of x-ticks
  const numXTicks = spacedData?.length;

  const handleResize = useCallback(() => {
    const width = calculateWidth(numXTicks * SEGMENT_WIDTH, container);
    if (chart?.current?.getChart) {
      const currentChart = chart.current.getChart();
      if (!currentChart) return;
      currentChart.changeSize(width, width * HEIGHT_TO_WIDTH_RATIO);
    }
  }, [numXTicks, container, chart]);

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [numXTicks, isLoading, handleResize]);

  return (
    <div
      className={`stops-bar ${addTabs ? 'stops-bar--tabs' : ''}`}
      ref={container}
      style={styles}
    >
      {isLoading ? (
        <Skeleton className="stops-bar__skeleton" />
      ) : (
        <Line
          ref={chart}
          {...props}
          {...config}
          className="stops-bar__chart"
          autoFit={false}
        />
      )}
    </div>
  );
};

export default StopsBar;
