import React, { useState } from 'react';
import { UnorderedListOutlined } from '@ant-design/icons';
import HeadingSection from '../../../common/components/HeadingSection';
import StatusCard from '../components/StatusCard';
import IntersectionsMap from '../components/IntersectionsMap';
import IntersectionsList from '../components/IntersectionsList';
import IntersectionsMapSettings from '../components/IntersectionsMapSettings';
import MapIcon from '../../../common/icons/Map';
import 'antd/dist/antd.css';
import './style.css';
import TabView from '../../../common/components/TabView';
import { useGetIntersectionsMapQuery, useGetStatusQuery } from '../api';

const View = {
  Map: 'Map',
  List: 'List',
};

const IntersectionsPage = () => {
  const [selectedStatus, setSelectedStatus] = useState([]);
  const [selectedMapIntersections, setSelectedMapIntersections] = useState([]);
  const [view, setView] = useState(View.Map);

  const { data: intersectionsMap, isLoading: isIntersectionsMapLoading } =
    useGetIntersectionsMapQuery();
  const { data: healthStatus, isLoading: isHealthStatusLoading } =
    useGetStatusQuery();

  return (
    <main className="IntersectionPage">
      <div className="heading-section-container">
        <HeadingSection title="Intersections" />
      </div>
      {!isHealthStatusLoading && healthStatus && (
        <StatusCard
          normal={healthStatus.normal}
          warning={healthStatus.warning}
          error={healthStatus.error}
        />
      )}
      <div className="error-attribution-container">
        <h4>Error Attribution</h4>
      </div>
      <TabView
        className="map-list"
        value={view}
        onChange={(value) => setView(value)}
        views={
          <>
            <MapIcon value={View.Map} />
            <UnorderedListOutlined value={View.List} />
          </>
        }
      >
        <div className="map-list__body">
          {view === View.Map && !isIntersectionsMapLoading && (
            <>
              <IntersectionsMapSettings
                intersections={intersectionsMap}
                selectedStatus={selectedStatus}
                setSelectedIntersections={setSelectedMapIntersections}
                setSelectedStatus={setSelectedStatus}
              />
              <IntersectionsMap
                className="map-list__settings"
                isMarkerShown
                intersections={intersectionsMap}
                selectedIntersections={selectedMapIntersections}
              />
            </>
          )}
          {view === View.List && <IntersectionsList />}
        </div>
      </TabView>
    </main>
  );
};

export default IntersectionsPage;
