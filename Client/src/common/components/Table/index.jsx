import React, { memo } from 'react';
import { Table as AntTable } from 'antd';

import TableSkeleton from './skeleton';

import 'antd/lib/table/style/css';
import './style.css';

/**
 * Comparator for two alphanumeric object values at key location (may be nested)
 *
 * @param dataIndex Value key. May include nested values. e.g. "field.nestedFieldA.nestedFieldB"
 */
export const alphanumericSorter = (dataIndex) => (a, b) => {
  if (!a && !b) return 0;
  if (!a) return -1;
  if (!b) return 1;

  const valueA = dataIndex.split('.').reduce((obj, prop) => obj[prop], a);
  const valueB = dataIndex.split('.').reduce((obj, prop) => obj[prop], b);

  return `${valueA}`.localeCompare(`${valueB}`);
};

const Table = ({ isLoading = false, pagination, ...antTableProps }) =>
  !isLoading ? (
    <AntTable
      {...antTableProps}
      pagination={
        pagination === false
          ? false
          : {
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} items`,
              ...pagination,
            }
      }
    />
  ) : (
    <TableSkeleton active={isLoading} />
  );

export default memo(Table);
