import { mapByGroup, statistics } from './array';

describe('mapByGroup', () => {
  test('basic even split', () => {
    const array = [
      { series: '1', value: 2 },
      { series: '1', value: 3 },
      { series: '1', value: 4 },
      { series: '2', value: 2 },
      { series: '2', value: 3 },
      { series: '2', value: 4 },
    ];

    const mappedArray = mapByGroup(
      array,
      'series',
      ({ value, ...rest }, index) => ({ ...rest, value: index + value })
    );

    expect(JSON.stringify(mappedArray)).toBe(
      JSON.stringify([
        { series: '1', value: 2 },
        { series: '1', value: 4 },
        { series: '1', value: 6 },
        { series: '2', value: 2 },
        { series: '2', value: 4 },
        { series: '2', value: 6 },
      ])
    );
  });

  test('empty series', () => {
    const array = [
      { series: '1', value: 2 },
      { series: '1', value: 3 },
      { series: '1', value: 4 },
      { value: 2 },
      { value: 3 },
      { value: 4 },
    ];

    const mappedArray = mapByGroup(
      array,
      'series',
      ({ value, ...rest }, index) => ({ ...rest, value: index + value })
    );

    expect(JSON.stringify(mappedArray)).toBe(
      JSON.stringify([
        { series: '1', value: 2 },
        { series: '1', value: 4 },
        { series: '1', value: 6 },
        { value: 2 },
        { value: 4 },
        { value: 6 },
      ])
    );
  });

  test('empty array', () => {
    const array = [];

    const mappedArray = mapByGroup(
      array,
      'series',
      ({ value, ...rest }, index) => ({ ...rest, value: index + value })
    );

    expect(JSON.stringify(mappedArray)).toBe('[]');
  });
});

describe('statistics', () => {
  test('basic min/max/sum/avg', () => {
    const array = [{ value: 2 }, { value: 3 }, { value: 4 }];

    const { min, max, sum, avg } = statistics(array, 'value');

    expect(min).toBe(2);
    expect(max).toBe(4);
    expect(sum).toBe(9);
    expect(avg).toBe(3);
  });

  test('with NaN', () => {
    const array = [{ value: 2 }, { value: Number.NaN }, { value: 4 }];

    const { min, max, sum, avg } = statistics(array, 'value');

    expect(min).toBe(2);
    expect(max).toBe(4);
    expect(sum).toBe(6);
    expect(avg).toBe(2);
  });

  test('with empty array', () => {
    const array = [];

    const { min, max, sum, avg } = statistics(array, 'value');

    expect(min).toBe(undefined);
    expect(max).toBe(undefined);
    expect(sum).toBe(undefined);
    expect(avg).toBe(undefined);
  });

  test('with undefined', () => {
    const array = undefined;

    const { min, max, sum, avg } = statistics(array, 'value');

    expect(min).toBe(undefined);
    expect(max).toBe(undefined);
    expect(sum).toBe(undefined);
    expect(avg).toBe(undefined);
  });
});
