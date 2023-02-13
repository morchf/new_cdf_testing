/* eslint-disable no-invalid-this */
import React from 'react';
import { Input } from 'antd';
import SearchOutlined from '../../icons/SearchOutlined';

import 'antd/lib/input/style/css';

// eslint-disable-next-line import/prefer-default-export
export const getColumnSearchProps = (
  dataIndex,
  { inputRef, placeholder = '' }
) => ({
  filterDropdown: ({ setSelectedKeys, selectedKeys, confirm }) => (
    <div style={{ padding: 8 }}>
      <Input
        allowClear
        ref={inputRef}
        placeholder={`Search ${placeholder}`}
        value={selectedKeys[0]}
        onChange={(e) => {
          setSelectedKeys(e.target.value ? [e.target.value] : []);
          confirm({ closeDropdown: false });
        }}
      />
    </div>
  ),
  filterIcon: (filtered) => (
    <SearchOutlined fill={filtered ? '#1890ff' : undefined} />
  ),
  onFilter: (value, record) =>
    record[dataIndex]
      ? record[dataIndex].toString().toLowerCase().includes(value.toLowerCase())
      : '',
  onFilterDropdownVisibleChange: (visible) => {
    if (visible) {
      setTimeout(() => inputRef.current.select(), 100);
    }
  },
});
