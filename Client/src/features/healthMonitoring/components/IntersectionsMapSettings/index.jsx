import React, { memo } from 'react';
import { Collapse, Select } from 'antd';

import TextHeader from '../../../../common/components/TextHeader';

import Legend from './Legend';
import './style.css';

const { Panel } = Collapse;
const { Option } = Select;

const IntersectionsMapSettings = ({
  intersections = [],
  setSelectedIntersections,
}) => {
  const onChange = (selected) => {
    setSelectedIntersections(selected);
  };

  return (
    <Collapse
      defaultActiveKey={['1']}
      expandIconPosition="right"
      className="map-settings"
    >
      <Panel
        header={<TextHeader size="h4">{'All Intersections'}</TextHeader>}
        key="1"
      >
        <div className="map-settings__settings">
          <Select
            mode="multiple"
            allowClear
            placeholder="Search (filterable drop-down list of intersections)"
            onChange={onChange}
          >
            {intersections.map((intersection) => (
              <Option
                key={`${intersection.latitude}-${intersection.longitude}`}
                value={intersection.locationname}
              >
                {intersection.locationname}
              </Option>
            ))}
          </Select>

          <div className="map-settings__legend">
            <Legend />
          </div>
        </div>
      </Panel>
    </Collapse>
  );
};

export default memo(IntersectionsMapSettings);
