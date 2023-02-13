import React, { memo } from 'react';
import './style.css';

const LegendItem = ({ color, route }) => (
  <div className="route__legend-item">
    <div
      className="route__legend-item__color-indicator"
      style={{ backgroundColor: color }}
    />
    <span>{`Route ${route.route}`}</span>
  </div>
);

export default memo(LegendItem);
