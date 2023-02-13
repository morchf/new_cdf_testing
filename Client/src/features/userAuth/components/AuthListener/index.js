import { useEffect } from 'react';
import { connect, useDispatch } from 'react-redux';
import { Auth, Hub } from 'aws-amplify';
import {
  loginUserSuccess,
  logoutUserSuccess,
  authUserFailure,
} from '../../store/slice';
import openNotification from '../../../../common/components/notification';
import {
  AUTH_FAILURE_REFRESH,
  AUTH_FAILURE_SIGNIN,
  AUTH_FAILURE_NOGROUP,
} from '../../constants';

const redirectUserToCognitoSignIn = async () => {
  await Auth.signOut({ opts: { global: true } });
  Auth.federatedSignIn();
}

const AuthListener = ({ children, userError }) => {
  const dispatch = useDispatch();
  useEffect(() => {
    let tokenPayload;

    // From https://docs.amplify.aws/lib/auth/social/q/platform/js/#setup-frontend
    Hub.listen('auth', async ({ payload: { event, data } }) => {
      try {
        switch (event) {
          case 'cognitoHostedUI':
            /**
             * dispatches user data
             * @todo for access token will need to pass in all signInUserSession
             */
            tokenPayload = data.signInUserSession.idToken.payload;
            if (!tokenPayload['cognito:groups']) {
              throw AUTH_FAILURE_NOGROUP;
            }
            dispatch(loginUserSuccess(tokenPayload));
            break;
          case 'tokenRefresh':
            // Amplify now handles this internally
            break;
          case 'signOut':
            dispatch(logoutUserSuccess());
            break;
          case 'oAuthSignOut':
            dispatch(logoutUserSuccess());
            break;
          case 'signIn_failure':
            throw AUTH_FAILURE_SIGNIN;
          case 'cognitoHostedUI_failure':
            throw AUTH_FAILURE_SIGNIN;
          case 'tokenRefresh_failure':
            throw AUTH_FAILURE_REFRESH;
          default:
        }
      } catch (error) {
        console.error(data);
        if (event !== userError) {
          openNotification({
            message: !error?.message ? 'Authentication Error' : error?.message,
            description: !error?.description ? `${error}` : error?.description,
          });
        }
        dispatch(authUserFailure(event));
        redirectUserToCognitoSignIn();
      }
    });

    const checkExistingUserData = async () => {
      try {
        const existingLoggedInUserInfo = await Auth.currentAuthenticatedUser();
        if (existingLoggedInUserInfo) {
          tokenPayload =
            existingLoggedInUserInfo.signInUserSession.idToken.payload;
          if (!tokenPayload['cognito:groups']) {
            throw AUTH_FAILURE_NOGROUP;
          }
          dispatch(loginUserSuccess(tokenPayload));
        }
      } catch (error) {
        if(error.message!=null)
        {
          dispatch(authUserFailure(error.message));
          redirectUserToCognitoSignIn();
        }
      }
    };

    checkExistingUserData();
  }, [dispatch, userError]);

  return children;
};



const mapStateToProps = (state) => {
  const { user } = state;
  return { userError: user.error };
};

export default connect(mapStateToProps)(AuthListener);
