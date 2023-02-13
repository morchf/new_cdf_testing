import React from 'react';

const Warning = ({ width = 14, height = 14, fill = '#CB3541', ...props }) => (
  <svg
    width={width}
    height={height}
    viewBox="0 0 14 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M13.933 12.375l-6.5-11.25A.494.494 0 007 .875a.493.493 0 00-.432.25l-6.5 11.25a.5.5 0 00.432.75h13a.5.5 0 00.433-.75zm-12.242-.436l5.31-9.19 5.309 9.19H1.69z"
      fill={fill}
    />
    <path
      d="M6.25 10.25a.75.75 0 101.5 0 .75.75 0 00-1.5 0zM6.5 5.5v2.875c0 .069.057.125.125.125h.75a.125.125 0 00.125-.125V5.5a.125.125 0 00-.125-.125h-.75A.125.125 0 006.5 5.5z"
      fill={fill}
    />
  </svg>
);

export default Warning;
