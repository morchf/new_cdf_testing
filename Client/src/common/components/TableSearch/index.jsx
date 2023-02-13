import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
import { Select } from 'antd';
import { compareWithTerm } from '../../utils/string';

import 'antd/lib/select/style/css';
import './style.css';

const { Option } = Select;

const TableSearch = ({
  data = [],
  direction,
  handleSearch = () => {},
  itemSearchField = 'route',
  searchKeys = [],
  title,
  dispatch,
  ...props
}) => {
  const [searchTerm, setSearchTerm] = useState();

  const options = useMemo(
    () =>
      [...(data || [])].sort((i1, i2) =>
        compareWithTerm(i1.route, i2.route, searchTerm)
      ),
    [data, searchTerm]
  );

  return (
    <div className="search-row">
      {title && <span>{title}</span>}
      <Select
        mode="multiple"
        onChange={handleSearch}
        onSearch={setSearchTerm}
        value={searchKeys}
        style={{ maxWidth: 496, minWidth: 248 }}
        allowClear
        {...props}
      >
        {options.map((item) => (
          <Option
            value={item[itemSearchField]}
            label={item[itemSearchField]}
            key={item[itemSearchField]}
          >
            {item[itemSearchField]}
          </Option>
        ))}
      </Select>
    </div>
  );
};

const mapStateToProps = ({ routeFilters }) => ({
  direction: routeFilters.direction,
});

export default connect(mapStateToProps)(TableSearch);
