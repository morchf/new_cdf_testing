import React, { memo } from 'react';

const Legend = () => (
  <ul className="legend__left">
    <li className="col-1">Legend</li>
    <li className="col-2">
      <div className="legend legend-1">normal</div>
      <div className="legend legend-2">warning</div>
      <div className="legend legend-3">error</div>
    </li>
    <li className="col-3">Error Status</li>
  </ul>
);

export default memo(Legend);
