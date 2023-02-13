import React, { memo, useEffect } from 'react';
import { Radio } from 'antd';

import './style.css';

const RoutesSelect = ({ routes, selectedRoutes, setSelectedRoutes }) => {
  useEffect(() => {
    const selectedY = document.querySelector(
      '.ant-radio-group.ant-radio-group-outline .ant-radio-wrapper.ant-radio-wrapper-checked'
    )?.offsetTop;
    const select = document.querySelector(
      '.ant-radio-group.ant-radio-group-outline'
    );

    if (selectedY) {
      select.scrollTop = selectedY - 100;
    }
  }, [routes]);

  const onChange = (e) => {
    setSelectedRoutes([e.target.value]);
  };

  const scrollToTop = () => {
    const checkboxGroup = document.querySelector('.ant-radio-group');
    checkboxGroup.scrollTop = 0;
  };

  return (
    <div className="map-settings__routes_multiselect">
      <div className="map-settings__routes_multiselect__top-row">
        <button onClick={scrollToTop}>{'^'}</button>
      </div>
      <Radio.Group onChange={onChange} value={selectedRoutes[0]}>
        {routes?.map((routesItem) => (
          <Radio
            key={`radio-${routesItem?.route}`}
            value={routesItem}
          >{`Route ${routesItem?.route}`}</Radio>
        ))}
      </Radio.Group>
    </div>
  );
};

export default memo(RoutesSelect);
