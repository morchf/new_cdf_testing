import React from 'react';

const StarOutlined = ({
  width = 14,
  height = 13,
  fill = '#00425F',
  ...props
}) => (
  <svg
    width={width}
    height={height}
    viewBox="0 0 14 13"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M13.197 4.513l-3.968-.577L7.456.34a.502.502 0 00-.897 0L4.786 3.936l-3.968.577a.499.499 0 00-.276.853l2.87 2.798-.678 3.952a.5.5 0 00.725.526l3.548-1.865 3.549 1.865a.5.5 0 00.725-.527l-.678-3.95 2.87-2.8a.499.499 0 00-.277-.852zM9.395 7.77l.564 3.286-2.952-1.55-2.951 1.552.564-3.286-2.388-2.328 3.3-.48 1.475-2.989 1.475 2.99 3.3.479L9.396 7.77z"
      fill={fill}
    />
  </svg>
);

export default StarOutlined;
