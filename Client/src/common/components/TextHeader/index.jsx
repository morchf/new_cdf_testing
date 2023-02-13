import React from 'react';
import './style.css';

const TextHeader = ({ children = null, size = 'h1' }) => {
  const WrapperElement = size;

  return <WrapperElement>{children}</WrapperElement>;
};

export default TextHeader;
