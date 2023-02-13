import React from 'react';
import { Typography as AntTypography } from 'antd';
import InfoTooltip from '../InfoTooltip';

import './style.css';

const { Title: AntTitle } = AntTypography;

const DataCard = ({ children, title, tooltipText }) => (
  <div className="data-card-container">
    <div className="title-row">
      <AntTitle level={3}>{title}</AntTitle>
      {tooltipText && <InfoTooltip text={tooltipText} />}
    </div>
    {children}
  </div>
);

export default DataCard;
