import React from 'react';
import { connect, useDispatch } from 'react-redux';
import { Redirect } from 'react-router-dom';
import { Spin } from 'antd';
import {
  ADMIN_LANDING_PAGE,
  AGENCY_LANDING_PAGE,
} from '../../../../common/constants';

const LoginCallback = ({ idToken, admin, error, agency }) => {
  if (idToken && admin) return <Redirect to={ADMIN_LANDING_PAGE} />;
  if (idToken && !admin) return <Redirect to={AGENCY_LANDING_PAGE} />;
  if (idToken && !agency) {
    return <Redirect to="/404" />;
  }
  if (error) {
    return <Redirect to="/400" />;
  }
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: '#0f9647',
        flexDirection: 'column',
        padding: '1em',
      }}
    >
      <Spin size="large" />
      <h2 style={{ color: '#1890ff' }}>Loading...</h2>
    </div>
  );
};

const mapStateToProps = ({ user }) => {
  const { idToken, admin, error, agency } = user;
  return { idToken, admin, error, agency };
};

export default connect(mapStateToProps)(LoginCallback);
