import React, { memo } from 'react';
import { Row, Col } from 'antd';
import DataCard from '../../../../common/components/DataCard';
import './style.css';
import { convertRelativeToPercentages } from '../../../../common/utils';

const StatusCard = ({ normal, warning, error }) => {
  const [p1, p2, p3] = convertRelativeToPercentages(
    [normal, warning, error],
    2
  );

  return (
    <DataCard title="Current Status" tooltipText="Some explaination of status">
      <Row className="status-row">
        <Col className="normal-col" span={8}>
          <p className="p1">Normal</p>
          <p className="p2">{normal}</p>
          <p className="p3">{p1}</p>
        </Col>
        <Col className="warning-col" span={8}>
          <p className="p1">Warning</p>
          <p className="p2">{warning}</p>
          <p className="p3">{p2}</p>
        </Col>
        <Col className="error-col" span={8}>
          <p className="p1">Error</p>
          <p className="p2">{error}</p>
          <p className="p3">{p3}</p>
        </Col>
      </Row>
    </DataCard>
  );
};

export default memo(StatusCard);
