import { TreeSelect as AntTreeSelect } from 'antd';
import { Compare, Period, SortBy, Timeframe } from '../../enums';
import './style.css';

const TIMEFRAME_KEY = 'timeframe';
const PERIOD_KEY = 'period';
const COMPARE_KEY = 'compare';
const SORT_BY_KEY = 'sort-by';

const timeframeOptions = [
  {
    value: `${TIMEFRAME_KEY} ${Timeframe.PeakAM}`,
    title: 'Peak AM',
  },
  {
    value: `${TIMEFRAME_KEY} ${Timeframe.PeakPM}`,
    title: 'Peak PM',
  },
  {
    value: `${TIMEFRAME_KEY} ${Timeframe.OffPeak}`,
    title: 'Off-peak',
  },
  {
    value: `${TIMEFRAME_KEY} ${Timeframe.Weekdays}`,
    title: 'Weekday',
  },
  {
    value: `${TIMEFRAME_KEY} ${Timeframe.Weekends}`,
    title: 'Weekend',
  },
];

const periodOptions = [
  {
    value: `${PERIOD_KEY} ${Period.Day}`,
    title: 'Day',
  },
  {
    value: `${PERIOD_KEY} ${Period.Week}`,
    title: 'Week',
  },
  {
    value: `${PERIOD_KEY} ${Period.Month}`,
    title: 'Month',
  },
  {
    value: `${PERIOD_KEY} ${Period.Year}`,
    title: 'Year',
  },
];

const compareOptions = [
  {
    value: `${COMPARE_KEY} ${Compare.Previous}`,
    title: 'Previous',
  },
];

const sortByOptions = [
  {
    value: `${SORT_BY_KEY} ${SortBy.MostRecent}`,
    title: 'Most recent',
  },
  {
    value: `${SORT_BY_KEY} ${SortBy.Earliest}`,
    title: 'Earliest',
  },
];

const treeData = [
  {
    value: TIMEFRAME_KEY,
    title: 'Timeframe',
    checkable: false,
    selectable: false,
    children: timeframeOptions,
  },
  {
    value: PERIOD_KEY,
    title: 'Period',
    checkable: false,
    selectable: false,
    children: periodOptions,
  },
  {
    value: COMPARE_KEY,
    title: 'Compare',
    checkable: false,
    selectable: false,
    children: compareOptions,
  },
  // {
  //   value: SORT_BY_KEY,
  //   title: 'Sort by',
  //   checkable: false,
  //   selectable: false,
  //   children: sortByOptions,
  // },
];

const categoriesAllowingMultiple = [TIMEFRAME_KEY];

const convertTreeValuesToObject = (values) => {
  const object = {};
  if (values) {
    values.forEach((treeValue) => {
      const [key, value] = treeValue.split(' ');
      const currentKeyValues = object[key];
      if (Array.isArray(currentKeyValues)) {
        object[key] = [value, ...currentKeyValues];
        return;
      }
      object[key] = currentKeyValues ? [value, currentKeyValues] : value;
    });
  }
  return object;
};

const convertObjectToTreeValues = (object) => {
  const treeValues = [];
  if (object) {
    Object.entries(object).forEach(([key, values]) => {
      if (Array.isArray(values)) {
        values.forEach((value) => treeValues.push(`${key} ${value}`));
        return;
      }
      treeValues.push(`${key} ${values}`);
    });
  }
  return treeValues;
};

const FilterTree = ({ filters, onFiltersChange }) => {
  const treeValues = convertObjectToTreeValues(filters);

  const handleChange = (values) => {
    const prefixes = new Set();
    const tv = values.reverse().filter((keyValue) => {
      const [prefix] = keyValue.split(' ');
      if (categoriesAllowingMultiple.includes(prefix)) return true;
      if (prefixes.has(prefix)) return false;
      prefixes.add(prefix);
      return true;
    });

    onFiltersChange(convertTreeValuesToObject(tv));
  };

  return (
    <div className="filter-tree">
      <AntTreeSelect
        className="filter-tree__filters ant-select-open"
        dropdownStyle={{ overflow: 'auto' }}
        treeData={treeData}
        value={treeValues}
        placeholder="Filters"
        treeCheckable
        allowClear
        multiple
        showArrow={true}
        onChange={handleChange}
      />
    </div>
  );
};

export default FilterTree;
