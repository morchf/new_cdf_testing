import React, { useState } from 'react';
import { Tabs, Skeleton } from 'antd';
import Map from '../Map';
import Card from '../Card';
import './style.css';

const MapTabs = ({
  tabs,
  tabsLoading,
  defaultActiveKey,
  map,
  children,
  ...props
}) => {
  const [activePane, setActivePane] = useState(defaultActiveKey);

  return (
    <Card paddingSize="none" className="map-tabs">
      {map || (
        <Map
          className="map-tabs__map"
          isLoading={false}
          isEmpty={true}
          selectedMapItemState={[]}
          gmapsShapes={[]}
          {...props}
        ></Map>
      )}
      <Card paddingSize="" className="map-tabs__tabs">
        {tabsLoading ? (
          <div className="tabs-skeleton">
            <Skeleton.Button
              active={true}
              style={{ height: 659, width: '100%' }}
            />
          </div>
        ) : (
          <Tabs defaultActiveKey={activePane} onChange={setActivePane}>
            {tabs}
          </Tabs>
        )}
      </Card>
      {children}
    </Card>
  );
};

export default MapTabs;
