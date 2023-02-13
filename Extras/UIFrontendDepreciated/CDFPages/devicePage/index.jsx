import React, { useEffect } from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import EditDevice from '../../components/EditDevice';
import openNotification from '../../../../common/components/notification';
import ConfigurationLayout from '../../../../common/layouts/ConfigurationLayout';
import { capitalizeFirstLetter } from '../../utils';
import useDevice from '../../hooks/useDevice';
import './style.css';

const DevicePage = ({ admin, match }) => {
  const { regname } = match.params;
  const { agyname } = match.params;
  const { vehname } = match.params;
  const { devname } = match.params;

  const capDevname = capitalizeFirstLetter(devname);

  // load device data
  const params = `/devices/${devname}`;
  const {
    device,
    isLoading,
    isError,
    error,
    editDeviceResponse,
    edit: editDevice,
  } = useDevice({ params });

  useEffect(() => {
    if (isError)
      openNotification({
        message: 'Error Retrieving Device Data',
        description: error.message,
      });
  }, [error?.message, isError]);

  return (
    <ConfigurationLayout title={capDevname} vehicle={vehname} device={devname}>
      <EditDevice
        device={device || ''}
        editDevice={editDevice}
        response={editDeviceResponse}
      />
    </ConfigurationLayout>
  );
};

const mapStateToProps = (state) => ({
  admin: state.user.admin,
});

export default connect(mapStateToProps, null)(withRouter(DevicePage));
