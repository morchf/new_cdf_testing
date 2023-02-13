import { DeviationCategory } from './constants';
import { filterItemsWithRouteFilters } from './utils';

// Convert array of times to object
const convertScheduleDeviationsToObjects = (arr) =>
  arr.map((scheduleDeviation) => ({
    avgScheduleDeviation: scheduleDeviation,
  }));

describe('filterItemsWithRouteFilters', () => {
  test('time band rounding positives', () => {
    const routes = convertScheduleDeviationsToObjects([
      5, 5, 4.5, 4.4, 4, 3.5, 3,
    ]);
    const filters = {
      timeRange: ['4', '5'],
    };
    const onTimeRange = [-5, 2];

    const filteredRoutes = filterItemsWithRouteFilters(
      filters,
      onTimeRange
    )(routes);

    expect(filteredRoutes.length).toBe(3);
    expect(
      filteredRoutes.find(
        ({ avgScheduleDeviation }) => +avgScheduleDeviation === 4
      )
    ).toBeTruthy();
  });

  test('time band rounding negatives', () => {
    const routes = convertScheduleDeviationsToObjects([
      -5.501, -5.5, -5.4, -5, -5, -4.5, -4.4, -4, -3,
    ]);
    const filters = {
      timeRange: ['-5', '-4'],
    };
    const onTimeRange = [-5, 2];

    const filteredRoutes = filterItemsWithRouteFilters(
      filters,
      onTimeRange
    )(routes);

    expect(filteredRoutes.length).toBe(3);
    // Check rounding direction is correct
    expect(
      filteredRoutes.find(
        ({ avgScheduleDeviation }) => +avgScheduleDeviation === -4
      )
    ).toBeTruthy();
  });

  test('deviation category exclusive - early', () => {
    const routes = convertScheduleDeviationsToObjects([
      5.501, 5.5, 5.4, 5, 5, 4.5, 4.4, 4, 3,
    ]);
    const filters = {
      deviationCategory: DeviationCategory.Early,
    };
    const onTimeRange = [-5, 5];

    const filteredRoutes = filterItemsWithRouteFilters(
      filters,
      onTimeRange
    )(routes);

    // Exclusive
    expect(filteredRoutes.length).toBe(3);
  });

  test('deviation category exclusive - late', () => {
    const routes = convertScheduleDeviationsToObjects([
      -5.501, -5.5, -5.4, -5, -5, -4.5, -4.4, -4, -3,
    ]);
    const filters = {
      deviationCategory: DeviationCategory.Late,
    };
    const onTimeRange = [-4.5, 5];

    const filteredRoutes = filterItemsWithRouteFilters(
      filters,
      onTimeRange
    )(routes);

    // Exclusive
    expect(filteredRoutes.length).toBe(5);
  });

  test('deviation category exclusive - on-time', () => {
    const routes = convertScheduleDeviationsToObjects([
      -5.501, -5.5, -5.4, -5, -5, -4.5, -4.4, -4, -3, 0, 1, 1.201, 3, 4, 5, 5,
      6,
    ]);
    const filters = {
      deviationCategory: DeviationCategory.OnTime,
    };
    const onTimeRange = [-4.5, 4];

    const filteredRoutes = filterItemsWithRouteFilters(
      filters,
      onTimeRange
    )(routes);

    // Inclusive
    expect(filteredRoutes.length).toBe(9);
  });
});
