import React, { memo } from 'react';
import { Switch } from 'antd';

import 'antd/lib/switch/style/css';
import './style.css';

const LabeledSwitch = ({ checked, label, onChange }) => (
  <div className="labeled-switch">
    <Switch checked={checked} onChange={onChange} />
    <span>{label}</span>
  </div>
);

export default memo(LabeledSwitch);
