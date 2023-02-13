/* eslint-disable no-plusplus */
import moment from 'moment';
import { Period } from '../../common/enums';
import { DeviationCategory } from './constants';

// eslint-disable-next-line import/prefer-default-export
export const getColor = () => {
  const letters = '0123456789ABCDEF';
  let color = '#';

  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }

  return color;
};

export const getDeviationCategory = (time, lateBand, earlyBand) => {
  if (time < lateBand) return DeviationCategory.Late;
  if (time > earlyBand) return DeviationCategory.Early;
  return DeviationCategory.OnTime;
};

export const getRouteDeviationLabel = (filters, onTimeRange) => {
  if (!filters || !Object.keys(filters).length) return 'Routes';

  const { deviationCategory, timeRange } = filters;
  const [lateBand, earlyBand] = onTimeRange;

  if (timeRange?.length === 2) {
    const [lower, upper] = timeRange;
    return `Routes from <${lower > 0 ? `+${lower}` : lower} to ${
      upper > 0 ? `+${upper}` : upper
    } Min>`;
  }

  if (deviationCategory === DeviationCategory.Late) {
    return `${deviationCategory} Routes (> ${lateBand} Min Late)`;
  }

  if (deviationCategory === DeviationCategory.Early) {
    return `${deviationCategory} Routes (> +${earlyBand} Min Early)`;
  }

  if (deviationCategory === DeviationCategory.OnTime) {
    return `${deviationCategory} Routes (${lateBand} to +${earlyBand} Min)`;
  }

  return 'Routes';
};

/**
 * Check if value is in time range. Inclusive lower for + and inclusive upper
 * for -
 * @param {number} value
 * @param {[number, number]} param1 Time band with lower and upper values
 * @return {boolean} If the value is in the time band
 */
export const isInTimeRange = (value, [lower, upper]) =>
  value > 0 ? value < upper && value >= lower : value > lower && value <= upper;

export const filterItemsWithRouteFilters =
  (filters, onTimeRange) => (array) => {
    if (!filters && !Object.keys(filters).length) return array;

    const { deviationCategory, timeRange } = filters;
    const [lateBand, earlyBand] = onTimeRange;

    // Filter to time band
    if (timeRange?.length === 2) {
      return array.filter((item) => {
        const value = +item.avgScheduleDeviation;
        return isInTimeRange(value, timeRange);
      });
    }

    // Filter within deviation category band
    if (deviationCategory === DeviationCategory.Early) {
      return array.filter((item) => +item.avgScheduleDeviation > earlyBand);
    }
    if (deviationCategory === DeviationCategory.Late) {
      return array.filter((item) => +item.avgScheduleDeviation < lateBand);
    }
    if (deviationCategory === DeviationCategory.OnTime) {
      return array.filter(
        (item) =>
          +item.avgScheduleDeviation < earlyBand + 0.001 &&
          +item.avgScheduleDeviation > lateBand - 0.001
      );
    }

    return array;
  };

const extractLst = ['earlyPercentage', 'latePercentage', 'onTimePercentage'];
export const transformColumnChartData = (chartData, isTime = true) => {
  const column = isTime === true ? 'period' : 'stopname';
  const res = chartData?.reduce((acc, cur) => {
    for (let i = 0; i < extractLst.length; i++) {
      const currStr = extractLst[i];
      const status = currStr.split('Percentage')[0];

      const newValue = {
        [column]: cur[column],
        status,
      };

      if (currStr in cur) {
        newValue.value = parseFloat(+cur[currStr]);
      }

      acc.push(newValue);
    }
    return acc;
  }, []);
  return res;
};
