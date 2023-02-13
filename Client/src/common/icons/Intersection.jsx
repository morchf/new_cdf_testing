import React from 'react';

const Intersection = ({ lowConfidence = false }) => (
  <svg
    width="22"
    height="20"
    viewBox="0 0 22 20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M14 2H8V7.5L1 7.5V12.5H8V18H14V12.5H21V7.5L14 7.5V2Z"
      fill={lowConfidence ? '#F08080' : '#F5F5FA'}
    />
    <path
      d="M8 3V4.5V7.5H2"
      stroke={lowConfidence ? 'red' : 'black'}
      strokeWidth="0.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M8 17V12.5H2"
      stroke={lowConfidence ? 'red' : 'black'}
      strokeWidth="0.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M14 3V7.5H20"
      stroke={lowConfidence ? 'red' : 'black'}
      strokeWidth="0.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M14 17V15.5V12.5H20"
      stroke={lowConfidence ? 'red' : 'black'}
      strokeWidth="0.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M8 10H1"
      stroke={lowConfidence ? 'red' : 'black'}
      strokeWidth="0.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray="4 4"
    />
    <path
      d="M21 10H14"
      stroke={lowConfidence ? 'red' : 'black'}
      strokeWidth="0.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray="4 4"
    />
  </svg>
);

export default Intersection;
