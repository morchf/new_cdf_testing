import { Layout } from 'antd';
import { Link } from 'react-router-dom';
import { connect } from 'react-redux';
import { useState, useEffect } from 'react';
import GttLogo from '../../../../common/icons/GttLogo';
import GttName from '../../../../common/icons/GttName';
import UserMenu from '../UserMenu';
import {
  ADMIN_LANDING_PAGE,
  AGENCY_LANDING_PAGE,
} from '../../../../common/constants';
import './style.css';

const { Header } = Layout;

// Check if string is all uppercase
const isUpperCase = (str) => str === str.toUpperCase();

// Format string to either all caps or title case
const formatString = (name) => {
  if (isUpperCase(name) === true) {
    return name;
  }
  const result = name
    .replace(/([_])/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase());
  return result;
};

const NavHeader = ({ idToken, admin, agency }) => {
  const [userTitle, setUserTitle] = useState('');
  const [homeLink, setHomeLink] = useState('');

  useEffect(() => {
    if (admin === true) {
      const adminTitle = 'Client Services';
      setUserTitle(adminTitle);
      return;
    }

    if (admin !== true && agency !== '' && agency !== undefined) {
      const agencyTitle = formatString(agency);
      setUserTitle(agencyTitle);
    }
  }, [admin, agency]);

  useEffect(() => {
    if (idToken && admin === true) {
      setHomeLink(ADMIN_LANDING_PAGE);
      return;
    }
    if (idToken && admin !== true) {
      setHomeLink(AGENCY_LANDING_PAGE);
    }
  }, [idToken, admin, agency]);

  return (
    <Header>
      <Link to={homeLink}>
        <GttLogo />
        <GttName />
      </Link>
      <UserMenu title={userTitle} />
    </Header>
  );
};

const mapStateToProps = ({ user }) => {
  const { idToken, agency, admin } = user;
  return { idToken, agency, admin };
};

export default connect(mapStateToProps)(NavHeader);
