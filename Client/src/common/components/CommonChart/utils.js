import moment from 'moment';
import { Period } from '../../enums';

export const getXAxisLabel = ({ dateRange: { startDate, endDate } }) => {
  let lastPeriod;
  let currentPeriod;

  // Show year if across year or a date year is different than current year
  const currentYear = moment().year();
  if (
    moment(startDate).year() !== currentYear ||
    moment(endDate).year() !== currentYear ||
    moment(startDate).diff(moment(endDate), 'year') > 0
  ) {
    lastPeriod = moment(startDate).format('MMM DD YYYY').toUpperCase();
    currentPeriod = moment(endDate).format('MMM DD YYYY').toUpperCase();
  } else {
    lastPeriod = moment(startDate).format('MMM DD').toUpperCase();
    currentPeriod = moment(endDate).format('MMM DD').toUpperCase();
  }

  return `${lastPeriod}-${currentPeriod}`;
};

export const maxLengthFormatter = (ref, maxLength = 15) =>
  ref?.length >= maxLength ? `${ref.slice(0, maxLength)}...` : ref;

export const getXAxisFormatterForFrequency = (frequency) => {
  if (frequency === Period.Year) return (ref) => moment(ref).format('YYY');
  if (frequency === Period.Month) return (ref) => moment(ref).format('MMM');
  if (frequency === Period.Week)
    return (ref) => moment(ref).format('DD').padStart(2, '0');
  if (frequency === Period.Day)
    return (ref) => moment(ref).format('DD').padStart(2, '0');

  return (value) => value;
};

export const wholeNumberFormatter = (number) => (+number).toFixed(0);

export const getXAxisFormatter = (isStop, frequency) => {
  if (isStop) return maxLengthFormatter;
  return getXAxisFormatterForFrequency(frequency);
};

export const isWeekend = (dateString) => {
  const dayOfWeek = moment(dateString).day();
  return dayOfWeek === 6 || dayOfWeek === 0; // 6 = Saturday, 0 = Sunday
};
