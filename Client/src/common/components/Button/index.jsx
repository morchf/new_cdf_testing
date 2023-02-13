import React, { memo } from 'react';
import './style.css';

const Button = ({
  className = '',
  onClick = null,
  children = 'Button Text',
  type = 'primary',
  size = 'md',
  disabled = false,
  location = '',
}) => (
  <button
    type="button"
    className={`btn btn-${
      disabled ? 'disabled' : type
    } btn-${size} btn-${location} ${className}`}
    onClick={onClick}
    disabled={disabled}
  >
    {children}
  </button>
);

export default memo(Button);
