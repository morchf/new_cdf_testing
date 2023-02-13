import './style.css';

const paddingSizeToClassNameMap = {
  none: null,
  s: 'padding-small',
  m: 'padding-medium',
  l: 'padding-large',
};

const Card = ({ paddingSize = 'm', className = '', children, ...props }) => (
  <div
    className={`card ${`card--${paddingSizeToClassNameMap[paddingSize]}`} ${className}`}
    {...props}
  >
    {children}
  </div>
);

export default Card;
