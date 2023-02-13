import React from 'react';

const DeltaUp = ({ fill = '#CB3541', width = 18, height = 11, ...props }) => (
  <svg
    width={width}
    height={height}
    viewBox="0 0 18 11"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M17.13 9.648L9.435.723a.586.586 0 00-.867 0L.87 9.648c-.286.333-.028.82.433.82h15.394c.462 0 .72-.487.434-.82z"
      fill={fill}
    />
  </svg>
);

export default DeltaUp;
