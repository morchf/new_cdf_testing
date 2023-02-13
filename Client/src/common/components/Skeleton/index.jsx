import { memo } from 'react';
import { Skeleton as AntSkeleton } from 'antd';
import './style.css';

const Skeleton = ({ number = 1, active = true, className = '', ...props }) => (
  <div className={`skeleton ${className}`} {...props}>
    {new Array(number).fill().map((_, index) => (
      <AntSkeleton.Button
        active={active}
        className="skeleton__item"
        key={index}
      />
    ))}
  </div>
);

export default memo(Skeleton);
