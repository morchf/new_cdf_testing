import React from 'react';
import Tooltip from '../Tooltip';
import Info from '../../icons/Info';
import './style.css';

const InfoTooltip = ({
  text = 'Description',
  className = '',
  danger,
  ...props
}) => (
  <div className={`info-tooltip ${className}`} {...props}>
    <Tooltip placement="right" title={text}>
      <Info danger={danger} />
    </Tooltip>
  </div>
);

export default InfoTooltip;
