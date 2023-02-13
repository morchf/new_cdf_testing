/**
 * DFS on object with node value and children provided by callback functions
 * @param {any} node Tree root node
 * @param {(any) => node[]} children Children of node
 * @param {(any) => boolean} equals Check for matching value
 * @return {any} Found value or 'null'
 */
export const dfs = (node, children = (n) => [], equals = (n) => false) => {
  if (node === undefined || node === null) return null;
  if (equals(node)) return node;

  const nodeChildren = children(node);

  if (!nodeChildren?.length) return null;

  for (let i = 0; i < nodeChildren.length; i++) {
    const matchingNode = dfs(nodeChildren[i], children, equals);
    if (matchingNode) return matchingNode;
  }

  return null;
};
