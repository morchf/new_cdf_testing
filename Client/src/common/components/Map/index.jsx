import React, { memo } from 'react';
import { Empty } from 'antd';
import GMaps from './GMaps';
import Skeleton from '../Skeleton';
import './style.css';

const Map = ({
  isLoading = false,
  isEmpty = false,
  gmapsShapes = [],
  selectedMapItemState = [null, () => {}],
  tooltips = {},
  onViewportBoundsChanged = () => {},
  children,
}) => (
  <>
    {isLoading && (
      <Skeleton number={1} className="map__skeleton" active={isLoading} />
    )}
    {isEmpty && !isLoading && (
      <div className="map__empty">
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    )}
    {!isLoading && !isEmpty && (
      <GMaps
        gmapsShapes={gmapsShapes}
        selectedMapItemState={selectedMapItemState}
        tooltips={tooltips}
        onViewportBoundsChanged={onViewportBoundsChanged}
      >
        {children}
      </GMaps>
    )}
  </>
);

export default memo(Map);
