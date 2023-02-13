import { Period } from '../enums';
import { fillEmptyDates } from './dateRange';

describe('fillEmptyDates', () => {
  test('short range with start and end empty', () => {
    const result = fillEmptyDates({
      array: [{ period: '2021-08-15' }],
      startDate: '2021-08-13',
      endDate: '2021-08-17',
      period: Period.Day,
      dateField: 'period',
    });

    expect(result.length).toBe(5);
    expect(result[0].period).toBe('2021-08-13');
    expect(result[result.length - 1].period).toBe('2021-08-17');
  });

  test('start after array start', () => {
    const result = fillEmptyDates({
      array: [
        { period: '2021-08-15' },
        { period: '2021-08-16' },
        { period: '2021-08-18' },
      ],
      startDate: '2021-08-17',
      period: Period.Day,
      dateField: 'period',
    });

    expect(result.length).toBe(2);
    expect(result[0].period).toBe('2021-08-17');
    expect(result[result.length - 1].period).toBe('2021-08-18');
  });

  test('end before array end', () => {
    const result = fillEmptyDates({
      array: [
        { period: '2021-08-15' },
        { period: '2021-08-16' },
        { period: '2021-08-18' },
      ],
      endDate: '2021-08-17',
      period: Period.Day,
      dateField: 'period',
    });

    expect(result.length).toBe(3);
    expect(result[0].period).toBe('2021-08-15');
    expect(result[result.length - 1].period).toBe('2021-08-17');
  });

  test('start date after end date', () => {
    fillEmptyDates({
      array: [{ period: '2021-08-15' }],
      startDate: '2021-08-19',
      endDate: '2021-08-17',
      period: Period.Day,
      dateField: 'period',
    });
  });
});
