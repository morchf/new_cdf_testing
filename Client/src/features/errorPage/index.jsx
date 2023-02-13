import React, { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import openNotification from '../../common/components/notification';
import NavHeader from '../navigation/components/NavHeader';
import { ErrorMessages } from '../../common/constants';
import './style.css';

const ErrorPage = ({ error, latestError }) => {
  const { body } = latestError || { body: { statusCode: 400 } };
  const { statusCode } = body;
  const [errorMessage, setErrorMessage] = useState(ErrorMessages[statusCode]);

  useEffect(() => {
    if (error) {
      /** @todo remove when using displayToUser on Logger Slice */
      openNotification({ message: 'Error', description: error });
    }
    setErrorMessage(ErrorMessages[statusCode]);
  }, [error, statusCode]);

  return (
    <div>
      <NavHeader />
      <div className="http-errors___scene">
        <div className="http-errors___text">
          <span className="http-errors___bg-code">{statusCode}</span>
          <span className="http-errors___msg">{errorMessage}</span>
          <span className="http-errors___support">
            {statusCode === 401 ? (
              <div>
                <span>
                  Permissions for this user do not allow access to this page
                </span>
                <span>
                  Please contact your GTT representative for permissions to view
                  this page
                </span>
              </div>
            ) : statusCode === 404 ? (
              <div>
                <span>No problem.</span>
                <span>We can fix that.</span>
                <span>
                  Just contact GTT client services to finish setting up your
                  agency.
                </span>
                <br />
                <a href="https://www.gtt.com/find-your-gtt-sales-representative/">
                  Find your representative here.
                </a>
              </div>
            ) : statusCode === 500 ? (
              <div>
                <span>Try refreshing your browser and sign in again.</span>
                <span>
                  It that doesn&apos;t work the application may be offline.
                </span>
                <span>
                  This is probably due to maintenance so please check back soon.
                </span>
                <span>Thank you for your patience.</span>
              </div>
            ) : (
              <div>
                <span>
                  Try signing in again and confirm the URL is correct.
                </span>
              </div>
            )}
          </span>
        </div>
      </div>
    </div>
  );
};

const mapStateToProps = ({ user, logger }) => {
  const { error } = user;
  const { latestError } = logger;
  return { error, latestError };
};

export default connect(mapStateToProps)(withRouter(ErrorPage));
