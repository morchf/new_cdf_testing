import { dfs } from './tree';

describe('dfs', () => {
  test('empty tree', () => {
    const matchingValue1 = dfs([]);
    expect(matchingValue1).toBeNull();

    const matchingValue2 = dfs(null);
    expect(matchingValue2).toBeNull();

    const matchingValue3 = dfs(undefined);
    expect(matchingValue3).toBeNull();
  });

  test('root', () => {
    const value = { key: 'b' };
    const matchingValue = dfs(
      value,
      () => null,
      ({ key }) => key === 'b'
    );
    expect(matchingValue).toBe(value);
  });

  test('child', () => {
    const value = { key: 'b' };
    const tree = {
      children: [value],
    };

    const matchingValue = dfs(
      tree,
      (node) => node.children,
      ({ key }) => key === 'b'
    );

    expect(matchingValue).toBe(value);
  });

  test('null child', () => {
    const value = { key: 'c' };
    const tree = {
      children: [null, value, null],
    };

    const matchingValue = dfs(
      tree,
      (node) => node.children,
      (node) => node?.key === 'c'
    );

    expect(matchingValue).toBe(value);
  });
});
