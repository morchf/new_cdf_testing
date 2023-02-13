import { Histogram as AntHistogram } from '@ant-design/charts';
import { Button as AntButton, Typography as AntTypography } from 'antd';
import { memo, useCallback, useEffect, useMemo, useRef } from 'react';
import { connect, useDispatch, useSelector } from 'react-redux';
import Skeleton from '../../../../common/components/Skeleton';
import { COLOR_ERROR } from '../../../../common/constants';
import { DeviationCategory } from '../../constants';
import { setFilters } from '../../store/slice';
import { getDeviationCategory, isInTimeRange } from '../../utils';
import { selectTimeRange } from '../../../featurePersistence/store/selectors';
import './style.css';

const { Title: AntTitle } = AntTypography;

const getColor = (
  deviationCategory,
  time,
  selectedDeviationCategory,
  selectedRange
) => {
  const isHidden =
    (selectedRange?.length === 2 && !isInTimeRange(time, selectedRange)) ||
    (selectedDeviationCategory &&
      deviationCategory !== selectedDeviationCategory);

  // Early (selected / unselected)
  if (deviationCategory === DeviationCategory.Early) {
    if (isHidden) return '#ffc91430';
    return '#ffc914';
  }

  // Late (selected / unselected)
  if (deviationCategory === DeviationCategory.Late) {
    if (isHidden) return `${COLOR_ERROR}30`;
    return COLOR_ERROR;
  }

  // Default (selected / unselected)
  if (isHidden) return '#99999930';
  return '#999999';
};

const getConfig = ({
  data,
  selectedDeviationCategory,
  selectedRange,
  averageTime,
  earlyBand,
  lateBand,
}) => {
  // Line is positioned relative to minimum x value
  const minTime = data && data.length ? +data[0].type : 0;
  const adjustedAverageTime = Math.abs(minTime) + averageTime;

  const getDeviationCategoryForRange = ([lower, upper]) => {
    const time = (upper + lower) / 2;
    return getDeviationCategory(time, lateBand, earlyBand);
  };

  return {
    data,
    binField: 'value',
    binWidth: 1,
    color: ({ range: [lower, upper] }) => {
      const time = (upper + lower) / 2;
      const deviationCategory = getDeviationCategoryForRange([lower, upper]);
      return getColor(
        deviationCategory,
        time,
        selectedDeviationCategory,
        selectedRange
      );
    },
    tooltip: {
      showTitle: false,
      formatter: ({ range: [lower, upper], count }) => {
        const deviationCategory = getDeviationCategoryForRange([lower, upper]);
        return {
          name: `${deviationCategory} (${lower} to ${upper} Min)`,
          value: `${count} Route${count > 1 ? 's' : ''}`,
        };
      },
    },
    yAxis: {
      label: {
        style: {
          fontWeight: 450,
          fill: 'black',
        },
      },
      title: {
        style: {
          fontWeight: 450,
          fill: 'black',
        },
        text: '# of Routes',
      },
    },
    xAxis: {
      title: {
        style: {
          fontWeight: 450,
          fill: 'black',
        },
        text: 'MINUTES +/-',
      },
    },
    legend: false,
    barWidthRatio: 0.2,
    barStyle: {
      radius: [20, 20, 0, 0],
    },
    // Add average line
    annotations: [
      {
        type: 'line',
        start: [adjustedAverageTime, 'min'],
        end: [adjustedAverageTime, 'max'],
        style: {
          lineWidth: 1,
          lineDash: [10, 7],
        },
      },
    ],
    animation: {
      appear: { animation: 'fade-in' },
    },
    interactions: [{ type: 'element-highlight' }],
    columnWidthRatio: 1,
    meta: {
      range: { tickInterval: 1 },
    },
  };
};

// eslint-disable-next-line react/display-name
const RadioCard = memo(({ value, onChange, earlyBand, lateBand }) => {
  const earlyLabel = `> +${earlyBand} Min Early`;
  const onTimeLabel = `On-time (${lateBand} to +${earlyBand} min)`;
  const lateLabel = `> ${lateBand} Min Late`;

  return (
    <div className="deviation-category__radio-card">
      <AntButton
        value={DeviationCategory.Late}
        onClick={onChange}
        className={`deviation-category__radio-button late ${
          value === DeviationCategory.Late ? 'active' : ''
        }`}
      >
        {lateLabel}
      </AntButton>

      <AntButton
        value={DeviationCategory.OnTime}
        onClick={onChange}
        className={`deviation-category__radio-button on-time ${
          value === DeviationCategory.OnTime ? 'active' : ''
        }`}
      >
        {onTimeLabel}
      </AntButton>
      <AntButton
        value={DeviationCategory.Early}
        onClick={onChange}
        className={`deviation-category__radio-button early ${
          value === DeviationCategory.Early ? 'active' : ''
        }`}
      >
        {earlyLabel}
      </AntButton>
    </div>
  );
});

const DeviationCategoryGraph = ({
  chart = [],
  isLoading,
  filters,
  onFiltersChange,
}) => {
  const { deviationCategory, timeRange: selectedRange } = filters;
  const onTimeRange = useSelector(selectTimeRange);
  const [lateBand, earlyBand] = onTimeRange;

  // For callback reference
  const selectedRangeRef = useRef(selectedRange);

  useEffect(() => {
    selectedRangeRef.current = selectedRange;
  }, [selectedRange]);

  const handleDeviationCategoryChange = useCallback(
    (newDeviationCategory) => {
      if (newDeviationCategory === deviationCategory) {
        onFiltersChange({});
        return;
      }
      onFiltersChange({ deviationCategory: newDeviationCategory });
    },
    [deviationCategory, onFiltersChange]
  );

  const handleEvent = (_, event) => {
    // Filter for click events on bars
    if (event.type === 'click' && event.data) {
      const { range: newRange } = event.data.data;
      const currentRange = selectedRangeRef.current;
      if (
        newRange?.length === 2 &&
        currentRange?.length === 2 &&
        newRange[0] === currentRange[0] &&
        newRange[1] === currentRange[1]
      ) {
        onFiltersChange({});
        return;
      }

      onFiltersChange({ timeRange: newRange });
    }
  };

  const config = useMemo(() => {
    let totalTime = 0;

    const data = chart.map(({ avgScheduleDeviation }) => {
      let value = +avgScheduleDeviation;
      totalTime += value;

      // Force negative values to map to correct bin (e.g. -1 -> [-1, -2])
      if (value < 0 && value % 1 === 0) {
        value -= 0.001;
      }

      return { value };
    });

    const averageTime = +(totalTime / chart?.length).toFixed(2);

    return getConfig({
      data: data || [],
      selectedDeviationCategory: deviationCategory,
      selectedRange,
      averageTime,
      earlyBand,
      lateBand,
    });
  }, [chart, earlyBand, lateBand, deviationCategory, selectedRange]);

  return (
    <section className="deviation-category">
      <AntTitle className="deviation-category__title" level={3}>
        Schedule Deviation
      </AntTitle>
      {isLoading ? (
        <Skeleton style={{ height: 500 }} />
      ) : (
        <>
          <AntHistogram
            className="deviation-category__chart"
            onEvent={handleEvent}
            autoFit
            {...config}
          ></AntHistogram>
          <RadioCard
            value={deviationCategory}
            onChange={(event) =>
              handleDeviationCategoryChange(event.target.value)
            }
            earlyBand={earlyBand}
            lateBand={lateBand}
          />
        </>
      )}
    </section>
  );
};

const mapStateToProps = ({ routeFilters, scheduleDeviation }) => {
  const { filters } = scheduleDeviation;

  return {
    filters: {
      ...filters,
      ...routeFilters,
    },
  };
};

const mapDispatchToProps = {
  onFiltersChange: (filters) => async (dispatch) =>
    dispatch(setFilters(filters)),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DeviationCategoryGraph);
