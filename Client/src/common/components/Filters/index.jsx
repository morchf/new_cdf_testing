import React, {
  memo,
  useCallback,
  useMemo,
  useEffect,
  useRef,
  useState,
  createRef,
} from 'react';
import { connect, useDispatch, useSelector } from 'react-redux';
import { Select, DatePicker, Button } from 'antd';
import moment from 'moment';
import { DATE_FORMAT, PERIODS, TooltipText } from '../../constants';
import {
  setDateRange,
  setDirection,
  setPeriods,
} from '../../../redux/routeFilters/slice';
import InfoTooltip from '../InfoTooltip';
import './style.css';
import Skeleton from '../Skeleton';
import { selectTimeperiod } from '../../../features/featurePersistence/store/selectors';

const { RangePicker } = DatePicker;

const MAX_DATE_RANGE_LENGTH = 90;

const LabeledEntry = ({ label, className, tooltip, children }) => (
  <div className={`labeled-select ${className}`}>
    <span>{label}</span>
    {tooltip && <InfoTooltip text={tooltip} />}
    {children}
  </div>
);

const maxDateDiff = (dates, date) =>
  dates?.length && (dates[0] || dates[1])
    ? Math.max(
        dates[0] ? date.diff(dates[0], 'days') : 0,
        dates[1] ? dates[1].diff(date, 'days') : 0
      )
    : 0;

const LabeledSelect = ({
  label,
  mode,
  options,
  handleChange,
  value,
  className,
  tooltip,
  ...props
}) => (
  <LabeledEntry label={label} tooltip={tooltip} className={className}>
    <Select
      mode={mode}
      style={{ width: '100%' }}
      placeholder={label}
      onChange={handleChange}
      options={options}
      value={value}
      {...props}
    />
  </LabeledEntry>
);

const LabeledRangePicker = ({
  isLoading,
  availability,
  label,
  handleChange,
  className,
  tooltip,
  value,
  ...props
}) => {
  const range = useMemo(() => {
    if (!value?.startDate || !value?.endDate) return undefined;
    return [moment(value.startDate), moment(value.endDate)];
  }, [value]);

  const [dates, setDates] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  const disabledDate = useCallback(
    (date) => {
      // Date range filtering
      if (!date || date > moment().endOf('day')) return true;

      // Availability period filtering. Only disable before agency was setup
      if (availability && date < availability.min) return true;

      // Selection range length filtering
      if (maxDateDiff(dates, date) > MAX_DATE_RANGE_LENGTH) {
        return true;
      }

      return false;
    },
    [dates, availability]
  );

  useEffect(() => {
    // Only trigger update if changed
    const isValidDateRange = dates && dates[0] && dates[1];
    const hasChanged =
      dates?.length &&
      (moment(dates[0]).diff(moment(range[0]), 'days') !== 0 ||
        moment(dates[1]).diff(moment(range[1]), 'days') !== 0);

    // Trigger date change
    if (!isOpen && isValidDateRange && hasChanged) {
      handleChange(dates);
    }
  }, [dates, handleChange, isOpen, range]);

  useEffect(() => {
    // Clear selected dates
    if (!isOpen) {
      setDates([]);
    }
  }, [isOpen]);

  const handleCalendarChange = useCallback(
    (...rest) => {
      const [_, [startDate, endDate], { range: rangeToSet }] = rest;

      const newStartDate =
        rangeToSet === 'start'
          ? moment(startDate)
          : (dates || [])[0] || range[0];
      const newEndDate =
        rangeToSet === 'end' ? moment(endDate) : (dates || [])[1] || range[1];

      const shouldClearOtherDate =
        !dates || newEndDate.diff(newStartDate, 'days') > MAX_DATE_RANGE_LENGTH;

      // If cleared dates
      if (rangeToSet === 'start') {
        setDates([newStartDate, shouldClearOtherDate ? undefined : newEndDate]);
        return;
      }

      setDates([shouldClearOtherDate ? undefined : newStartDate, newEndDate]);
    },
    [dates, range]
  );

  const handleClear = (_, [startDate, endDate], ...rest) => {
    // Clear selection on 'x'
    if (!startDate && !endDate) {
      setDates(undefined);
    }
  };

  const element = createRef();
  const handleOk = () => {
    // Partial range update
    if (dates) {
      setDates([dates[0] || range[0], dates[1] || range[1]]);
    }

    // Clear user-focus on partial update
    element?.current.blur();

    setIsOpen(false);
  };

  // Show current selection (included cleared selections)
  const displayValue = useMemo(
    () => (isOpen && (!dates || dates?.length) ? dates : range),
    [dates, isOpen, range]
  );

  return (
    <LabeledEntry label={label} tooltip={tooltip} className={className}>
      {isLoading ? (
        <Skeleton className="filters-container__button" />
      ) : (
        <RangePicker
          ref={element}
          renderExtraFooter={() => (
            <Button
              type="primary"
              size="small"
              className="filters-container__ok"
              onClick={handleOk}
            >
              Ok
            </Button>
          )}
          onCalendarChange={handleCalendarChange}
          onChange={handleClear}
          value={displayValue}
          open={isOpen}
          onOpenChange={setIsOpen}
          disabledDate={disabledDate}
          format={DATE_FORMAT}
          style={{ width: '100%' }}
          {...props}
        />
      )}
    </LabeledEntry>
  );
};

const Filters = ({
  isLoading,
  availability,
  dateRange,
  direction,
  isPeriodSingleSelect,
  periods,
  agencyPeriods,
}) => {
  const dispatch = useDispatch();

  const timeperiod=useSelector(selectTimeperiod);

  const handleDirection = (value) => dispatch(setDirection(value));
  const handleDateRange = ([startDate, endDate]) => {
    dispatch(
      setDateRange({
        startDate: moment(startDate).format(DATE_FORMAT),
        endDate: moment(endDate).format(DATE_FORMAT),
      })
    );
  };

  // Force at least one enabled period
  const handlePeriods = (value) => value?.length && dispatch(setPeriods(value));

  // Lock inputs to sticky container
  const container = useRef();
  const getPopupContainer = () => container.current;

  return (
    <div className="filters-container" ref={container}>
      <LabeledSelect
        label="Direction"
        value={direction}
        handleChange={handleDirection}
        options={[
          {
            label: 'Inbound',
            value: 'inbound',
          },
          {
            label: 'Outbound',
            value: 'outbound',
          },
          {
            label: 'All',
            value: 'all',
          },
        ]}
        getPopupContainer={getPopupContainer}
      />
      <LabeledRangePicker
        isLoading={isLoading}
        availability={availability}
        label="Date Range"
        tooltip={TooltipText.DateRange}
        value={dateRange}
        handleChange={handleDateRange}
        getPopupContainer={getPopupContainer}
      />
      {timeperiod[0] &&
      <LabeledSelect
        label="Time"
        className={`filters-container__time ${
          periods?.length === 1 && 'filters-container__time--single-value'
        }`}
        mode={!isPeriodSingleSelect && 'multiple'}
        value={periods}
        handleChange={handlePeriods}
        options={agencyPeriods}
        getPopupContainer={getPopupContainer}
      />
      }
    </div>
  );
};

const mapStateToProps = ({ routeFilters }) => {
  const { dateRange, direction, periods } = routeFilters;

  return { dateRange, direction, periods };
};

export default memo(connect(mapStateToProps)(Filters));
