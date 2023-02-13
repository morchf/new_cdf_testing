// Error openNotification messages
export const ERROR_NOT_SUPPORTED =
  '405 - Smart Cities Platform does not currently support multiple agencies for a user.';
export const ERROR_NOT_CONFIGURED =
  '404 - User has no assigned agency. Contact GTT client services to configure agency permissions for this user.';
export const ERROR_NOT_SETUP =
  '404 - Agency has no data, please contact your GTT representative to finish setting up agency';
export const ERROR_NO_DATA = '404 - No data available for selected filters';

// Error object for filling in content of ErrorPage component
export const ErrorMessages = {
  400: 'We were unable to process your request',
  401: 'Unauthorized',
  404: 'Agency not found:',
  500: 'Internal Server Error:',
};
