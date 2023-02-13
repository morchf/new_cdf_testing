import React, { memo } from 'react';
import { Row, Col, Empty } from 'antd';
import DataCard from '../../../../common/components/DataCard';
import './style.css';
import Skeleton from '../../../../common/components/Skeleton';
import { convertRelativeToPercentages } from '../../../../common/utils';

const OverallCard = ({ noData, early, isLoading, late, onTime, tooltip }) => {
  // Use 'num' instead of 'percentage' as 'percentage' is rounded
  const [onTimeP2, earlyP2, lateP2] = convertRelativeToPercentages([
    onTime?.num,
    early?.num,
    late?.num,
  ]);

  const onTimeP3 = onTime && `${onTime?.num}/${onTime?.totalNum} Routes`;
  const lateP3 = late && `${late?.num}/${late?.totalNum} Routes`;
  const earlyP3 = early && `${early?.num}/${early?.totalNum} Routes`;

  return (
    <DataCard title="Overall Performance" tooltipText={tooltip}>
      {isLoading ? (
        <Skeleton className="overall-card__skeleton" active={isLoading} />
      ) : noData === false ? (
        <Row className="status-row">
          <Col className="ontime-col" span={8}>
            <p className="p1">On-time</p>
            <p className="p2">{onTimeP2}</p>
            <p className="p3">{onTimeP3}</p>
          </Col>
          <Col className="late-col" span={8}>
            <p className="p1">Late</p>
            <p className="p2">{lateP2}</p>
            <p className="p3">{lateP3}</p>
          </Col>
          <Col className="early-col" span={8}>
            <p className="p1">Early</p>
            <p className="p2">{earlyP2}</p>
            <p className="p3">{earlyP3}</p>
          </Col>
        </Row>
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </DataCard>
  );
};

export default memo(OverallCard);
