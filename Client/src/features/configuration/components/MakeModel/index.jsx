import React from 'react';
import { Tag } from 'antd';
import { makeColorMap, modelColorMap } from '../../../../common/constants';

// Creates tag for data in the make/model column of table
// Calls makeModelColorPicker to determine appropriate color
const MakeModel = ({ makeModel, ...props }) => (
  <>
    {makeModel?.map((entry) => {
      if (entry === '') return null;
      const color =
        entry in makeColorMap ? makeColorMap[entry] : modelColorMap[entry];

      return (
        <Tag color={color} key={entry} {...props}>
          {entry}
        </Tag>
      );
    })}
  </>
);

export default MakeModel;
