import React from 'react';

const CircleIndicator = ({
  fill = '#CB3541',
  height = 12,
  stroke = '#EAE9F0',
  strokeWidth = 2,
  width = 12,
  ...props
}) => (
  <svg
    width={width}
    height={height}
    viewBox="0 0 12 12"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M10.834 6c0 2.775-2.215 5-4.917 5C3.214 11 1 8.775 1 6s2.214-5 4.917-5c2.702 0 4.917 2.225 4.917 5z"
      fill={fill}
      stroke={stroke}
      strokeWidth={strokeWidth}
    />
  </svg>
);

export default CircleIndicator;
