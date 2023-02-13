import { compareWithTerm } from './string';

describe('compareWithTerm', () => {
  test('no term', () => {
    const string1 = '1';
    const string2 = '12';
    const term = null;

    expect(compareWithTerm(string1, string2, term)).toBe(-1);
  });

  test('matching term', () => {
    const string1 = '1';
    const string2 = '12';
    const term = '1';

    expect(compareWithTerm(string1, string2, term)).toBe(-1);
  });

  test('matching longer term', () => {
    const string1 = '1';
    const string2 = '12';
    const term = '12';

    expect(compareWithTerm(string1, string2, term)).toBe(1);
  });

  test('matching term suffix', () => {
    const string1 = '1';
    const string2 = '21';
    const term = '1';

    expect(compareWithTerm(string1, string2, term)).toBe(-1);
  });

  test('sort array', () => {
    const strings = ['13', '21', '1', '121', '12'];
    const term = '1';

    expect(
      JSON.stringify(strings.sort((s1, s2) => compareWithTerm(s1, s2, term)))
    ).toBe(JSON.stringify(['1', '12', '121', '13', '21']));
  });
});
