import { useMemo } from 'react';
import { searchTermFilter } from '../utils';

const useSearchTermFilter = (searchTerm, array, field) =>
  useMemo(
    () => searchTermFilter(searchTerm, array, field),
    [searchTerm, array, field]
  );

export default useSearchTermFilter;
