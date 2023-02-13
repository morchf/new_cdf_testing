import React, { memo } from 'react';
import Button from '../Button';
import './style.css';

const ButtonRadioGroup = ({
  active = null,
  buttons = [],
  setActive = null,
  size = 'md',
}) => (
  <div className="button-select">
    {buttons.map((buttonProps) => {
      const handleClick = () => setActive(buttonProps.name);

      return (
        <Button
          className="margin-right"
          key={buttonProps.name}
          onClick={handleClick}
          size={size}
          type={active === buttonProps.name ? 'primary' : 'secondary'}
          {...buttonProps}
        />
      );
    })}
  </div>
);

export default memo(ButtonRadioGroup);
