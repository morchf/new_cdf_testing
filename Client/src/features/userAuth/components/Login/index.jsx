import React from 'react';
import { useDispatch } from 'react-redux';
import { Auth } from 'aws-amplify';
import { loginUserRequest } from '../../store/slice';
import Button from '../../../../common/components/Button';
import logo from '../../gtt_logo.jpg';

const Login = () => {
  const dispatch = useDispatch();
  sessionStorage.setItem('disclaimerCount', '0');
  return (
    <div className="Login">
      <img className="logo" src={logo} alt="Logo" />
      <h1>Opticom Cloud</h1>
      <br /> <br />
      <Button
        type="login"
        size="lg"
        location="center"
        onClick={() => {
          dispatch(loginUserRequest());
          Auth.federatedSignIn();
        }}
      >
        Sign In
      </Button>
    </div>
  );
};
export default Login;
