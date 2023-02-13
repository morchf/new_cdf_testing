import { AWS_REGION } from '../../common/constants';

export const config = {
  Auth: {
    region: process.env.REACT_APP_AWS_REGION,
    userPoolId: process.env.REACT_APP_USER_POOL_ID,
    userPoolWebClientId: process.env.REACT_APP_SC_CLIENT_ID,
    oauth: {
      domain: `${process.env.REACT_APP_SC_DOMAIN_NAME}.auth.${AWS_REGION}.amazoncognito.com`,
      scope: ['openid'],
      redirectSignIn: process.env.REACT_APP_CALLBACK_URL,
      redirectSignOut: process.env.REACT_APP_LOGOUT_URL,
      responseType: 'code', // or 'token', note that REFRESH token will only be generated when the responseType is code
    },
  },
};
