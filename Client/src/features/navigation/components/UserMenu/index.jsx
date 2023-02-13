import React from 'react';
import { useDispatch } from 'react-redux';
import { DownOutlined } from '@ant-design/icons';
import { Menu, Dropdown } from 'antd';
import { Auth } from 'aws-amplify';
import { logoutUserRequest } from '../../../userAuth/store/slice';

import './style.css';

const UserMenu = ({ title }) => {
  const dispatch = useDispatch();
  const signOut = () => {
    dispatch(logoutUserRequest);
    Auth.signOut({ opts: { global: true } });
  };

  const menu = (
    <Menu>
      <Menu.Item className="user-menu__item" key="signOut" onClick={signOut}>
        Sign Out
      </Menu.Item>
    </Menu>
  );

  return (
    <Dropdown overlay={menu}>
      <a className="user-menu__dropdown" onClick={(e) => e.preventDefault()}>
        <p className="user-menu__title">{title}</p>
        <DownOutlined />
      </a>
    </Dropdown>
  );
};

export default UserMenu;
