import { convertRelativeToPercentages, createShortTimeLabel } from '.';

describe('convertRelativeToPercentages', () => {
  test('rounding with decimals', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([0.107, 0.134, 0.216]);

    expect(p1).toBe('23%');
    expect(p2).toBe('29%');
    expect(p3).toBe('48%');
  });

  test('rounding with decimals above 100', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([
      369.398, 646.813, 2528.209,
    ]);

    expect(p1).toBe('10%');
    expect(p2).toBe('18%');
    expect(p3).toBe('72%');
  });

  test('single item', () => {
    const [p1] = convertRelativeToPercentages([33]);

    expect(p1).toBe('100%');
  });

  test('splits total greater than 100% with 0% at end', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([0.925, 0.075, 0.0]);

    expect(p1).toBe('93%');
    expect(p2).toBe('7%');
    expect(p3).toBe('0%');
  });

  test('splits total greater than 100%', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([72.5, 27.5, 0]);

    expect(p1).toBe('73%');
    expect(p2).toBe('27%');

    // Should not be -1%
    expect(p3).toBe('0%');
  });

  test('odd equal splits', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([33, 33, 33]);

    expect(p1).toBe('33%');
    expect(p2).toBe('33%');
    expect(p3).toBe('34%');
  });

  test('even equal splits', () => {
    const [p1, p2] = convertRelativeToPercentages([1, 1]);

    expect(p1).toBe('50%');
    expect(p2).toBe('50%');
  });

  test('greater than 100% splits', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([15, 22, 9]);

    expect(p1).toBe('33%');
    expect(p2).toBe('48%');
    expect(p3).toBe('19%');
  });

  test('decimal precision', () => {
    const [p1, p2, p3] = convertRelativeToPercentages([15, 22, 9], 2);

    expect(+p1.slice(0, -1) + +p2.slice(0, -1) + +p3.slice(0, -1)).toBe(100);
    expect(p1).toBe('32.61%');
    expect(p2).toBe('47.83%');
    expect(p3).toBe('19.56%');
  });
});

describe('createShortTimeLabel', () => {
  test('minute with seconds from decimal', () => {
    const minutes = 1.34;
    const result = createShortTimeLabel(minutes);

    expect(result).toBe('80\nsec');
  });

  test('rounding seconds goes to 30 seconds and should increase 1 minute', () => {
    const minutes = 1.499; // 1m 30s -> 2m
    const result = createShortTimeLabel(minutes);

    expect(result).toBe('90\nsec');
  });
});
