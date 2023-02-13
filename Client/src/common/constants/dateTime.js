import moment from 'moment';

// Dates and time
export const DATE_FORMAT = 'YYYY-MM-DD';
export const DATE_TIME_READABLE_FORMAT = 'M/D/YYYY h:mmA';

/**
 * Production TODAY: Current date
 * QA TODAY: 2022-04-20
 * Dev, others TODAY: 2021-12-29
 */
let today;
if (process.env.REACT_APP_SC_DOMAIN_NAME === 'opticom-cloud') {
  today = moment().format(DATE_FORMAT);
} else if (process.env.REACT_APP_SC_DOMAIN_NAME === 'cdfmanager-test') {
  today = moment('2022-04-20', DATE_FORMAT);
} else {
  today = moment('2021-12-29', DATE_FORMAT);
}

export const TODAY = moment(today).format(DATE_FORMAT);
export const WEEK_AGO = moment(today).subtract(6, 'days').format(DATE_FORMAT);
export const MONTH_AGO = moment(today)
  .subtract(1, 'months')
  .format(DATE_FORMAT);
export const YEAR_AGO = moment(today).subtract(1, 'years').format(DATE_FORMAT);

export const START_DATES_BY_RANGE = {
  month: MONTH_AGO,
  week: WEEK_AGO,
  year: YEAR_AGO,
};
