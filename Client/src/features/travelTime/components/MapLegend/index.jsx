import React from 'react';
import { Metric } from '../../../../common/enums';
import BusStop from '../../../../common/icons/BusStop';
import Intersection from '../../../../common/icons/Intersection';
import './style.css';

const MapLegend = ({ selectedMetric }) => (
  <>
    {selectedMetric === Metric.SignalDelay ? (
      <div className="map-legend map-legend-signal-delay">
        <h3>Legend</h3>
        <p>Intersection</p>
        <Intersection />
        <p>Low # of Trips</p>
        <Intersection lowConfidence={true} />
      </div>
    ) : selectedMetric === Metric.DwellTime ? (
      <div className="map-legend map-legend-dwell-time">
        <h3>Legend</h3>
        <p>Stop</p>
        <BusStop size={'small'} />
        <p>Low # of Trips</p>
        <BusStop size={'small'} lowConfidence={true} />
      </div>
    ) : selectedMetric === Metric.DriveTime ? (
      <div className="map-legend map-legend-drive-time">
        <h3>Legend</h3>
        <p>Stop</p>
        <BusStop size={'small'} />
      </div>
    ) : null}
  </>
);

export default MapLegend;
