import React from 'react';

const DeltaDown = ({ fill = '#393', width = 17, height = 11, ...props }) => (
  <svg
    width={width}
    height={height}
    viewBox="0 0 17 11"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M16.197.531H.803c-.461 0-.72.488-.433.82l7.697 8.926c.22.255.644.255.867 0l7.697-8.925c.286-.333.028-.82-.434-.82z"
      fill={fill}
    />
  </svg>
);

export default DeltaDown;
