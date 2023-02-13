import React, { useEffect, useState, useRef } from 'react';
import { Layout } from 'antd';
import SideMenu from '../SideMenu';
import NavHeader from '../NavHeader';

import 'antd/lib/layout/style/css';
import './style.css';

const { Sider } = Layout;

const NavWrapper = ({ children, ...props }) => {
  const menuWidth = 256;
  const collapsedMenuWidth = 80;

  const contentRef = useRef();
  const [isCollapsed, setCollapsed] = useState(false);

  useEffect(() => {
    contentRef.current = document.querySelector('.ant-layout.content');
  }, []);

  useEffect(() => {
    contentRef.current.style.marginLeft = isCollapsed
      ? `${collapsedMenuWidth}px`
      : `${menuWidth}px`;
  }, [isCollapsed]);

  const onCollapse = (collapsed) => {
    setCollapsed(collapsed);
  };

  return (
    <>
      <NavHeader />
      <Layout className="layout">
        <Sider
          collapsible
          collapsed={isCollapsed}
          onCollapse={onCollapse}
          width={menuWidth}
          collapsedWidth={collapsedMenuWidth}
          theme="light"
        >
          <SideMenu />
        </Sider>
        <Layout className="content">{children}</Layout>
      </Layout>
    </>
  );
};

export default NavWrapper;
