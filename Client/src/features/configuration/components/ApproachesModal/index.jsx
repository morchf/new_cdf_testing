import React, { useState } from 'react';
import Draggable from 'react-draggable';
import { Input, Checkbox } from 'antd';
import { PlusOutlined, MinusOutlined } from '@ant-design/icons';
import './style.css';

const { Search } = Input;

const ApproachesModal = ({ drawingManager,generalData }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleSetCreate = (e) => {
    if (e.target.checked)
      // eslint-disable-next-line no-undef
      drawingManager.setDrawingMode(google.maps.drawing.OverlayType.POLYLINE);
    else drawingManager.setDrawingMode(null);
  };

  const handleMeasure = (e) => {};

  return (
    <Draggable>
      <div className="approaches-modal">
        <div className="approaches-modal-top">
          <h2 className="approaches-modal-title">
            <b>{generalData.intersectionName}</b>
          </h2>
          <div className="approaches-modal-collapse">
            {isCollapsed ? (
              <PlusOutlined
                className="collapse-button"
                onClick={() => setIsCollapsed(false)}
              />
            ) : (
              <MinusOutlined
                className="collapse-button"
                onClick={() => setIsCollapsed(true)}
              />
            )}
          </div>
          <h3>{generalData.latitude}, {generalData.longitude}</h3>
        </div>
        {!isCollapsed && (
          <div className="approaches-modal-bottom">
            <h2>Approaches Map Tools</h2>
            <div className="approaches-modal-tools">
              <p>Create Approach</p>
              <Checkbox
                onChange={handleSetCreate}
                style={{ margin: '0px 20px 0px 5px' }}
              />
            </div>
          </div>
        )}
      </div>
    </Draggable>
  );
};

export default ApproachesModal;
