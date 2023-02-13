import { notification } from 'antd';
import 'antd/lib/notification/style/css';

const openNotification = ({
  message = 'Notification Title',
  description = 'Notification text.',
  type = 'error',
  duration = 10,
}) => {
  notification[type]({
    message,
    description,
    key: `open-${Date.now()}`,
    duration,
  });
};

export default openNotification;
