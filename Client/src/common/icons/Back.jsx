import React from 'react';

const Back = ({ fill = '#0290D4', width = 17, height = 17, ...props }) => (
  <svg
    width={width}
    height={height}
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M14.656 7.821H4.043l6.352-5.428a.142.142 0 00-.094-.25H8.696a.294.294 0 00-.19.07L1.65 8.067a.571.571 0 00-.2.43.563.563 0 00.2.432l6.895 5.891c.027.023.06.036.094.036h1.66c.134 0 .196-.164.094-.25l-6.35-5.429h10.613c.08 0 .145-.064.145-.143V7.964a.144.144 0 00-.145-.143z"
      fill={fill}
    />
  </svg>
);

export default Back;
