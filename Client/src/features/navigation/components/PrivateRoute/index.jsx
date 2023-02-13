// A wrapper for <Route>
import React from 'react';
import { Route, Redirect } from 'react-router-dom';
import { connect } from 'react-redux';
import { getStoredToken } from '../../utils';

const PrivateRoute = ({ userToken, children, ...rest }) => {
  const idToken = userToken != null ? userToken : getStoredToken();

  return (
    <Route
      {...rest}
      render={() => (idToken ? children : <Redirect to="/login" />)}
    />
  );
};

const mapStateToProps = ({ user }) => ({ userToken: user.idToken });
export default connect(mapStateToProps)(PrivateRoute);
