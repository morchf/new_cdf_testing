import React from 'react';
import { Radio } from 'antd';
import './style.css';

const Button = ({ value, children, ...props }) => (
  <Radio.Button className="mini-radio__button" value={value} {...props}>
    {children}
  </Radio.Button>
);

const Group = ({ defaultValue, children, className = '', ...props }) => (
  <Radio.Group
    className={`mini-radio ${className}`}
    defaultValue={defaultValue}
    size="small"
    {...props}
  >
    {children}
  </Radio.Group>
);

export default { Button, Group };
