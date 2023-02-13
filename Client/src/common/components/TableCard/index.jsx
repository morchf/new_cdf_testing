import React from 'react';
import { Typography as AntTypography } from 'antd';
import './style.css';
import InfoTooltip from '../InfoTooltip';

const { Title: AntTitle } = AntTypography;

const TableCard = ({
  title,
  tooltip,
  controls,
  table,
  children,
  vertical = false,
  className = '',
  titleLevel = 5,
}) => (
  <section
    className={`table-card ${!title ? 'table-card--empty' : ''} ${className}`}
  >
    {title && (
      <div
        className={`table-card__header ${
          vertical ? 'table-card__header--vertical' : ''
        }`}
      >
        <AntTitle className="table-card__title" level={5}>
          {title}
          {tooltip && <InfoTooltip text={tooltip} />}
        </AntTitle>
        <div className="table-card__controls">{controls}</div>
      </div>
    )}
    <div className="table-card__table">
      {table}
      {children}
    </div>
  </section>
);

export default TableCard;
