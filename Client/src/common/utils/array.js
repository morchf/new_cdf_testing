export const uniqueItems = (array, id = () => String.toString) =>
  !array?.length
    ? []
    : array.reduce(
        ({ unique, uniqueIds }, item) => ({
          unique: uniqueIds.has(id(item)) ? unique : [...unique, item],
          uniqueIds: uniqueIds.add(id(item)),
        }),
        { unique: [], uniqueIds: new Set() }
      ).unique;

/**
 * Take a number of items from the array according to a predicate
 * @param {any[]} array Array to be filtered
 * @param {number} num Maximum number of items to take
 * @param {(any, any[], number) => boolean} predicate Predicate function given the item, taken items, and index
 * @return {any[]} Filtered array
 */
export const take = (array, num, predicate) => {
  if (!array?.length) return [];
  if (!predicate) return array.slice(0, num) || [];

  const taken = [];
  array.forEach((item, ...rest) => {
    if (taken.length === num) return;
    if (predicate(item, taken, ...rest)) {
      taken.push(item);
    }
  });

  return taken;
};

/**
 * Run mapping function across each group individually, groupping by field name
 * @param {any[]} array Array to be grouped and mapped
 * @param {string} fieldName Name of field used for grouping
 * @param {any} mapper Mapping function
 * @return {any[]} Mapped array by group
 */
export const mapByGroup = (array, fieldName, mapper) => {
  const groups = array.reduce((groupMap, item) => {
    const existingGroup = groupMap[item[fieldName]];
    if (existingGroup) {
      existingGroup.push(item);
    } else {
      groupMap[item[fieldName]] = [item];
    }

    return groupMap;
  }, {});

  const mappedGroups = Object.values(groups).map((group) => group.map(mapper));
  return mappedGroups.reduce((items, group) => [...items, ...group], []);
};

/**
 * Calculate the min, max, sum, and avg of an array
 * @param {any[]} array
 * @param {string} fieldName Field name for min/max/sum/avg
 */
export const statistics = (array, fieldName) => {
  const { min, max, sum } = (array || []).reduce(
    ({ min: currMin, max: currMax, sum: currSum }, item) => {
      if (
        item[fieldName] === null ||
        item[fieldName] === undefined ||
        Number.isNaN(item[fieldName])
      )
        return { min: currMin, max: currMax, sum: currSum };

      const value = +item[fieldName];
      return {
        min: Math.min(
          currMin === undefined ? Number.MAX_SAFE_INTEGER : currMin,
          value
        ),
        max: Math.max(
          currMax === undefined ? Number.MIN_SAFE_INTEGER : currMax,
          value
        ),
        sum: (currSum === undefined ? 0 : currSum) + value,
      };
    },
    {}
  );

  return {
    min,
    max,
    sum,
    avg: sum === undefined ? sum : sum / array?.length,
  };
};
