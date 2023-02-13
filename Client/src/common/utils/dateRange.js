import moment from 'moment';
import { DATE_FORMAT } from '../constants';
import { Period } from '../enums';

export const TIME_LABEL_MAP = {
  [Period.Day]: 'Day',
  [Period.Week]: 'Week',
  [Period.Month]: 'Month',
  [Period.Year]: 'Year',
};

export const dateRangeFormatter = (startDateRaw, dateRangeLength) => {
  const startDate = moment(startDateRaw);

  const endOfRange = moment(startDate).add(dateRangeLength, 'days');
  return dateRangeLength === 0 ||
    endOfRange.diff(moment(startDate), 'days') === 0
    ? startDate.format(DATE_FORMAT)
    : `${startDate.format(DATE_FORMAT)} to ${endOfRange.format(DATE_FORMAT)}`;
};

export const fillEmptyDates = ({
  array,
  startDate: startDateMaybe,
  endDate: endDateMaybe,
  period = Period.Day,
  dateField = 'period',
}) => {
  if (!array.length) return [];

  // Incremement each item using the period of time between each
  const incrementDate = (date) =>
    moment(date).add(1, period).format(DATE_FORMAT);

  // Compare dates
  const compare = (date1, date2) => moment(date1).diff(date2, `${period}s`);
  const isEqual = (date1, date2) => compare(date1, date2) === 0;

  const sortedArray = array.sort((item1, item2) =>
    item1[dateField].localeCompare(item2[dateField])
  );
  const filledArray = [];

  let startDate = startDateMaybe || sortedArray[0][dateField];
  let endDate = endDateMaybe || sortedArray[sortedArray.length - 1][dateField];

  if (compare(startDate, endDate) > 0) {
    const startDateHolder = startDate;
    startDate = endDate;
    endDate = startDateHolder;
  }

  let currentDate = startDate;
  while (compare(currentDate, endDate) <= 0) {
    // eslint-disable-next-line no-loop-func
    const matchingDate = sortedArray.find((item) =>
      isEqual(item[dateField], currentDate)
    );

    if (matchingDate) {
      filledArray.push(matchingDate);
    } else {
      filledArray.push({ [dateField]: currentDate });
    }

    currentDate = incrementDate(currentDate);
  }

  return filledArray;
};
