import { useMemo } from 'react';
import { DIRECTIONS } from '../constants';

const useRoutesSearchKeysFilter = (searchKeys = [], array = []) =>
  useMemo(() => {
    if (!searchKeys || !searchKeys.length) {
      return array || [];
    }

    const searchKeysArray = searchKeys.map((key) => {
      const pieces = key.split('-');

      if (!pieces?.length) return ['', ''];

      // Handles names with '-'
      const direction = pieces[pieces.length - 1];
      if (DIRECTIONS.includes(direction))
        return [pieces.slice(0, -1).join('-'), direction];

      return [pieces.join('-'), ''];
    });

    return array.filter(
      (item) =>
        !!searchKeysArray.find(([route, direction]) =>
          item.direction && direction
            ? item.route === route && item.direction === direction
            : item.route === route
        )
    );
  }, [searchKeys, array]);

export default useRoutesSearchKeysFilter;
