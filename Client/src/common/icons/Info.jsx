import React from 'react';

const Info = ({
  fill = '#323140',
  width = 15,
  height = 16,
  danger = false,
  ...props
}) => (
  <svg
    width={width}
    height={height}
    viewBox="0 -1 15 15"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M7.253.5a7 7 0 100 14 7 7 0 000-14zm0 12.813a5.813 5.813 0 010-11.626 5.813 5.813 0 010 11.626z"
      fill={fill}
    />
    <path
      d="M6.503 4.75a.75.75 0 101.5 0 .75.75 0 00-1.5 0zM7.628 6.5h-.75a.125.125 0 00-.125.125v4.25c0 .069.056.125.125.125h.75a.125.125 0 00.125-.125v-4.25a.125.125 0 00-.125-.125z"
      fill={fill}
    />
    {danger && (
      <g stroke="red" strokeWidth="3" fill="black">
        <circle id="danger" cx="11.25" cy="2.5" r="1.5" />
      </g>
    )}
  </svg>
);

export default Info;
