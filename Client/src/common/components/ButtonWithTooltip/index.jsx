import { Tooltip } from 'antd';
import Button from '../Button';

const ButtonWithTooltip = ({
  buttonText = '',
  tooltipText = '',
  disabled = false,
  ...props
}) => (
  <Tooltip title={tooltipText}>
    <span style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}>
      <Button disabled={disabled} {...props}>
        {buttonText}
      </Button>
    </span>
  </Tooltip>
);

export default ButtonWithTooltip;
