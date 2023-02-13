import moment from 'moment';
import { DATE_TIME_READABLE_FORMAT } from '../constants';

/**
 * Format decimal time values into readable min and sec
 * @param {number} minDecimal Minutes in decimals
 * @param {number} precision Number of decimal places after seconds
 * @return {string} Formatted time value to desired precision e.g. 5m 03s or 37.8s
 */

const humanizeDecimalMinutes = (minDecimal, precision = 0) => {
  if (minDecimal == null || Number.isNaN(+minDecimal)) return null;

  const sign = minDecimal < 0 ? '-' : '';
  let min = Math.floor(Math.abs(minDecimal));

  // remove decimals after seconds if displaying sec and mins
  precision = min > 0 ? 0 : precision;
  const secDecimal = ((Math.abs(minDecimal) * 60) % 60).toFixed(precision);
  let sec = Math.abs(+secDecimal) < 0.0001 ? 0 : secDecimal;

  if (sec === 60) {
    sec = 0;
    min++;
  }

  if (Number.isNaN(min)) return null;

  const minutes = `${min === 0 ? '' : sign}${min}m`;
  const seconds = `${sec < 10 && !precision ? '0' : ''}${sec}s`;

  if (sec === 0) return minutes;
  if (min === 0) return `${sign}${seconds}`;

  return `${minutes} ${seconds}`;
};

/**
 * Remove '-' and add label 'ahead' to positive and 'behind' to negative values.
 * @param {number} minutes Minutes in decimal
 * @return {string} Value, units (sec/min) and label
 */
const humanizeDeviationLabel = (minDecimal) => {
  const formatted = humanizeDecimalMinutes(minDecimal);

  return parseFloat(formatted) < 0
    ? `${formatted.slice(1)} behind`
    : `${formatted} ahead`;
};

const getPeak = (peak) => {
  const startHour = +peak.start_time.split(':')[0];
  const startMin = peak.start_time.split(':')[1];
  const startH = ((startHour + 11) % 12) + 1;
  const endHour = +peak.end_time.split(':')[0];
  const endMin = peak.end_time.split(':')[1];
  const endH = ((endHour + 11) % 12) + 1;
  const m = endHour > 12 ? 'pm' : 'am';
  return `${startH}:${startMin} - ${endH}:${endMin} ${m}`;
};

const getPeakValues = (peakAM,peakPM) => (
  { 
    peakAM: getPeak(peakAM), 
    peakPM: getPeak(peakPM)
  }
);

/**
 * Convert seconds to shorthand minutes or seconds with units (sec/min)
 * @param {number} minutes Minutes
 * @param {number} [maxSeconds] Max number of seconds before converting to minutes
 * @return {string} Newline separated value and units (sec/min)
 */
export const createShortTimeLabel = (minutes, maxSeconds = 999) => {
  if (Number.isNaN(Number(minutes))) {
    return '--\nNo Data';
  }

  const seconds = Math.round(+minutes * 60);

  if (seconds <= maxSeconds) {
    return `${seconds}\nsec`;
  }

  const value = seconds >= 60 ? Math.round(+seconds / 60) : seconds;
  const units = seconds >= 60 ? 'min' : 'sec';

  return `${value}\n${units}`;
};

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const readableDateTimeFormatter = (dateTime) =>
  moment(dateTime).format(DATE_TIME_READABLE_FORMAT);

/**
 * Filter the array given a search term
 * @param {string} [searchTerm] Search term used to match objects
 * @param {any[]} values
 * @param {string} [key] Key of object. Matched on object directly, otherwise
 * @return {any[]} Array of filtered values
 */
const searchTermFilter = (searchTerm, values, key) => {
  if (!values || !values.length) return [];
  if (!searchTerm) return values;

  const lowerCaseSearchTerm = searchTerm.toLowerCase();
  return values.filter((value) =>
    (key ? value[key] : value).toLowerCase().includes(lowerCaseSearchTerm)
  );
};

const handleReduxFetch =
  ({
    request,
    onSuccess = () => {},
    onError = () => {},
    onLoadingChange = () => {},
  }) =>
  async (dispatch) => {
    dispatch(onLoadingChange(true));
    try {
      const response = await request();

      if (!Object.keys(response).length) {
        throw new Error('Unable to retrieve data');
      }

      dispatch(onSuccess(response));
    } catch (e) {
      onError(e);
    } finally {
      dispatch(onLoadingChange(false));
    }
  };

/**
 * Reducing several variants of a map route line into one route loop.
 * @param {any[]} routeData Raw data from backend.
 * [
    {
      "date": "2021-09-01",
      "route": "1",
      "segments": [
        {
            "points": [
                {
                    "lat": "37.795436",
                    "lon": "-122.396968",
                    "progress": "0.0"
                },
                {
                    "label": "Clay St & Drumm St",
                    "lat": "37.795436",
                    "lon": "-122.396819",
                    "progress": "0.0014163556264037715"
                },
                ...
            ],
            "stopendname": "Sacramento St & Davis St",
            "stopstartname": "Clay St & Drumm St"
        },
        ...
      ],
      "shape": "189975"
    },
    {
      "date": "2021-09-01", <-- Same date
      "route": "1", <-- Same route
      "segments": [ <-- Other set of segments
        ...
      ],
      "shape": "189976"
    }
  ]
 * @return {any} An object where each key stands for a route name,
 * and its segments[] field contains segments of all the route variants.
 * {
    1: {
      date: '2021-09-01',
      route: '1',
      segments: [ <-- Segments from all items with the same item.route
        {
          points: [
            {
              lat: '37.795436',
              lon: '-122.396968',
              progress: '0.0'
            },
            {
              label: 'Clay St & Drumm St',
              lat: '37.795436',
              lon: '-122.396819',
              progress: '0.0014163556264037715'
            },
            ...
          ]
        },
        ...
      ],
      shape: '189975',
    }
  }
 */
const reduceSegments = (routeData) => {
  const reduced = routeData?.length
    ? routeData.reduce((acc, item) => {
        if (acc[item.route]) {
          return {
            ...acc,
            [item.route]: {
              ...acc[item.route],
              segments: [...acc[item.route].segments, ...item.segments],
            },
          };
        }

        return {
          ...acc,
          [item.route]: item,
        };
      }, {})
    : [];

  return Object.values(reduced || {});
};

const capitalize1stLetter = (string) =>
  !string ? '' : string[0].toUpperCase() + string.substring(1);

/**
 * Convert an array of relative values to a percentage string representation.
 * Clamps percentage values to equal 100% exactly
 *
 * @param {number[]} splits Array of numbers giving relative percentage of total
 * @param {number} precision Number of digits after the decimal
 * @return {string[]} Array in same order of the relative value as a percentage
 */
const convertRelativeToPercentages = (
  splits,
  precision = 0,
  formatter = (value) => `${value}%`
) => {
  const sum = splits.reduce((acc, split) => acc + +split, 0);
  let percentageLeft = 100;
  return splits.map((split, index) => {
    const percentage = split ? ((+split / sum) * 100).toFixed(precision) : 0;

    // Clamp to total 100%
    if (index === splits.length - 1) {
      return formatter(Math.max(percentageLeft, 0).toFixed(precision));
    }

    // Adjust for rounding over 100%
    const currPercentage = formatter(
      Math.min(percentage, percentageLeft).toFixed(precision)
    );
    percentageLeft -= percentage;
    return currPercentage;
  });
};

/**
 * Create a new object with specified key-value pairs
 * @param {object} object Object
 * @param {string[]} keys Array of keys
 * @return {object} Passed in object with only filtered key-value pairs
 */
const filterObjectValues = (object, keys) =>
  Object.entries(object || {}).reduce((acc, [key, value]) => {
    if (!keys.includes(key)) {
      return acc;
    }
    return {
      ...acc,
      [key]: value,
    };
  }, {});

// @todo - Implement a real error handler
const errorHandler = (error, errorInfo) => {
  console.log('Logging', error, errorInfo);
};

const accessLocalStorage = () => {
  const storeLocalItem = (key, value) => {
    localStorage.setItem(key, value);
  };
  const getLocalItem = (key) => localStorage.getItem(key);
  return { storeLocalItem, getLocalItem };
};

export {
  capitalize1stLetter,
  humanizeDecimalMinutes,
  humanizeDeviationLabel,
  getPeakValues,
  reduceSegments,
  wait,
  readableDateTimeFormatter,
  searchTermFilter,
  handleReduxFetch,
  convertRelativeToPercentages,
  filterObjectValues,
  errorHandler,
  accessLocalStorage,
};
