import React from 'react';
import { Tooltip as AntTooltip } from 'antd';

import 'antd/lib/tooltip/style/css';

const Tooltip = ({ children, ...props }) => (
  <AntTooltip
    {...props}
    color={'white'}
    overlayInnerStyle={{ color: '#323140' }}
  >
    {children}
  </AntTooltip>
);

export default Tooltip;
