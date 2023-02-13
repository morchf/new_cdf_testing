import React, { memo } from 'react';
import { Collapse, Divider } from 'antd';
import TextHeader from '../TextHeader';
import LegendItem from './LegendItem';
import RoutesSelect from './RoutesSelect';
import RouteNamesListSkeleton from './skeleton';

import 'antd/lib/checkbox/style/css';
import 'antd/lib/collapse/style/css';
import 'antd/lib/divider/style/css';
import './style.css';

const { Panel } = Collapse;

const MapSettings = ({
  routes = [],
  isMapLoading,
  selectedRoutes,
  setSelectedRoutes,
  withLegend = true,
}) => (
  <Collapse
    defaultActiveKey={['1']}
    expandIconPosition="right"
    className="map-settings"
  >
    <Panel header={<TextHeader size="h4">{'View Routes'}</TextHeader>} key="1">
      <div className="map-settings__settings">
        {!isMapLoading && routes.length ? (
          <RoutesSelect
            routes={routes}
            selectedRoutes={selectedRoutes}
            setSelectedRoutes={setSelectedRoutes}
          />
        ) : (
          <RouteNamesListSkeleton active={isMapLoading} />
        )}
        {withLegend ? (
          <div>
            <Divider />
            <div className="map-settings__routes">
              {!isMapLoading && routes.length ? (
                routes.map((route) => (
                  <LegendItem
                    key={`route-${route.route}`}
                    color={route.color}
                    route={route}
                  />
                ))
              ) : (
                <RouteNamesListSkeleton active={isMapLoading} />
              )}
            </div>
          </div>
        ) : null}
      </div>
    </Panel>
  </Collapse>
);

export default memo(MapSettings);
