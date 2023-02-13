import React, { useState, useMemo, useEffect } from 'react';
import { Menu } from 'antd';
import {
  MonitorOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { connect } from 'react-redux';
import { Link, useLocation, withRouter } from 'react-router-dom';
import TrafficLight from '../../../../common/icons/TrafficLight';
import { dfs } from '../../../../common/utils/tree';

/** @todo remain commented until included feature release */
// import Monitoring from '../../../../common/icons/Monitoring';
import Configuration from '../../../../common/icons/Configuration';
// import Dashboard from '../../../../common/icons/Dashboard';

import 'antd/lib/menu/style/css';
import './style.css';

const { SubMenu } = Menu;

const notAdminMenuStructure = [
  // {
  //   title: 'DASHBOARD',
  //   icon: <Dashboard className="side-menu__icon" />,
  //   key: 'dashboard',
  //   items: [{ key: '1', title: 'Option 1', disabled: true }],
  // },
  /** @TODO uncomment once Vehicle Health Monitoring infrastructure is in place */
  // {
  //   title: 'HEALTH MONITORING',
  //   icon: <MonitorOutlined className="side-menu__icon" />,
  //   key: 'health-monitoring',
  //   items: [
  //     {
  //       key: 'vehicles-health-monitoring',
  //       title: 'Vehicles',
  //       to: '/health-monitoring/vehicles',
  //     },
  //   ],
  // },
  {
    title: 'ANALYTICS',
    icon: <BarChartOutlined className="side-menu__icon" />,
    key: 'analytics',
    items: [
      {
        key: 'transit-delay',
        title: 'Transit Delay',
        to: '/analytics/transit-delay',
      },

      {
        key: 'schedule-deviation',
        title: 'Schedule Deviation',
        to: '/analytics/schedule-deviation',
      },
      // { key: 'stop-rate', title: 'Stop Rate', disabled: true },
    ],
  },
  // {
  //   title: 'HEALTH MONITORING',
  //   icon: <Monitoring className="side-menu__icon" />,
  //   key: 'health-monitoring',
  //   items: [
  //     {
  //       key: 'intersections',
  //       title: 'Intersections',
  //       to: '/health-monitoring/intersections',
  //     },
  //     { key: 'vehicles', title: 'Vehicles', disabled: true },
  //   ],
  // },
  // {
  //   title: 'CONFIGURATION',
  //   icon: <Configuration className="side-menu__icon" />,
  //   key: 'configuration',
  //   items: [
  //     {
  //       key: 'intersection-devices',
  //       title: 'Intersection Devices',
  //       disabled: true,
  //     },
  //     { key: 'vehicle-devices', title: 'Vehicle Devices', disabled: true },
  //   ],
  // },
];

const SideMenu = ({ admin, region, agency, match }) => {
  const { intersectionName } = match.params;

  const [selectedKey, setSelectedKey] = useState('transit-delay');
  const [openKey, setOpenKey] = useState('analytics');

  const menuStructure = useMemo(() => {
    if (admin === true) {
      setOpenKey('configuration');
      setSelectedKey('agency');
      const adminMenuStructure = notAdminMenuStructure.concat([
        {
          title: 'CONFIGURATION',
          icon: <SettingOutlined className="side-menu__icon" />,
          key: 'configuration',
          items: [
            {
              key: 'agency',
              title: 'Agency Settings',
              to: `/region/${region}/agency/${agency}`,
            },
            {
              key: 'intersections',
              title: 'Intersections',
              to: `/region/${region}/agency/${agency}/intersections`,
            },
            {
              key: 'vehicles',
              title: 'Vehicles',
              to: `/region/${region}/agency/${agency}/vehicles`,
            },
            {
              key: 'vps',
              title: 'VPS',
              to: `/region/${region}/agency/${agency}/vps`,
            },
          ],
        },
      ]);
      return adminMenuStructure;
    }
    return notAdminMenuStructure;
  }, [admin, region, agency]);

  const { pathname } = useLocation();

  // Match selected items in menu structure to current URL
  useEffect(() => {
    const matchingItem = dfs(
      { items: menuStructure },
      ({ items }) => items,
      ({ to }) => to === pathname
    );

    if (matchingItem && matchingItem.key !== openKey) {
      setSelectedKey(matchingItem.key);
    }
  }, [admin, pathname, menuStructure, openKey]);

  return (
    <Menu
      mode="inline"
      theme="light"
      style={{ borderRight: 0 }}
      defaultOpenKeys={[openKey]}
      selectedKeys={[selectedKey]}
      onSelect={({ key }) => setSelectedKey(key)}
    >
      {menuStructure.map((subMenu) =>
        subMenu.items.length ? (
          <SubMenu
            className="side-menu__sub-menu"
            key={subMenu.key}
            icon={subMenu.icon}
            title={subMenu.title}
          >
            {subMenu.items.map((item) => (
              <Menu.Item
                className="side-menu__item"
                key={item.key}
                icon={item.icon}
                disabled={item.disabled}
              >
                <Link to={item.to || '/'}>{item.title}</Link>
              </Menu.Item>
            ))}
          </SubMenu>
        ) : (
          <Menu.Item
            className="side-menu__item"
            key={subMenu.key}
            icon={subMenu.icon}
          >
            {subMenu.title}
          </Menu.Item>
        )
      )}
    </Menu>
  );
};

const mapStateToProps = ({ user }) => {
  const { admin, agency, region } = user;
  return { admin, agency, region };
};

export default connect(mapStateToProps)(withRouter(SideMenu));
