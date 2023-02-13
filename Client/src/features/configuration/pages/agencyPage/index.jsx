import React, { useEffect, useState } from 'react';
import { connect, useDispatch, useSelector } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { Select, TimePicker, Card } from 'antd';
import UploadStaticIntersections from '../../components/UploadStaticIntersections';
import EditAgency from '../../components/EditAgency';
import EditAgencySettings from '../../components/EditAgencySettings';
import ConfigurationLayout from '../../../../common/layouts/ConfigurationLayout';
import openNotification from '../../../../common/components/notification';
import useAgencies from '../../hooks/useAgencies';
import useFeaturePersistence from '../../../featurePersistence/hooks/useFeaturePersistence';
import useAgency from '../../hooks/useAgency';
import {
  setTimeperiod,
  setOnTimeRange,
} from '../../../featurePersistence/store/slice';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../../featurePersistence/store/selectors';
import { capitalizeFirstLetter } from '../../utils';
import './style.css';

const AgencyPage = ({ admin, match }) => {
  const { regname, agyname } = match.params;
  const capAgyname = capitalizeFirstLetter(agyname);

  const timeperiod = useSelector(selectTimeperiod);
  const onTimeRange = useSelector(selectTimeRange);

  // load agency data
  let params = `/groups/%2F${regname}%2F${agyname}`;
  const {
    agency,
    isLoading: isLoadingAgencyInfo,
    isError: agencyIsError,
    error: agencyError,
    editAgencyResponse,
    edit: editAgency,
  } = useAgency({ params });

  const {
    agency: agencyinfo,
    isLoading: agencyInfoIsLoading,
    isError: agencyInfoIsError,
    error: agencyInfoError,
    editFeaturePersistanceTSPResponse,
    editFeaturePersistanceTSP,
  } = useFeaturePersistence();
  const dispatch = useDispatch();
  useEffect(() => {
    if (!agencyInfoIsLoading) {
      dispatch(
        setTimeperiod([
          {
            start_time: agencyinfo?.Feature?.peak_am_range?.start_time,
            label: 'peak_am',
            end_time: agencyinfo?.Feature?.peak_am_range.end_time,
          },
          {
            start_time: agencyinfo?.Feature?.peak_pm_range.start_time,
            label: 'peak_pm',
            end_time: agencyinfo?.Feature?.peak_pm_range.end_time,
          },
        ])
      );
      dispatch(
        setOnTimeRange([
          parseInt(agencyinfo?.Feature?.late_schedule_deviation_limit, 10),
          parseInt(agencyinfo?.Feature?.early_schedule_deviation_limit, 10),
        ])
      );
    }
  }, []);

  const { Option } = Select;

  params = `/groups/%2F${regname}/members/groups`;
  const {
    agenciesList,
    isError: agenciesIsError,
    error: agenciesError,
  } = useAgencies({ params });

  useEffect(() => {
    if (agencyIsError)
      openNotification({
        message: 'Error Getting Agency Data',
        description: agencyError.message,
      });
  }, [agencyError?.message, agencyIsError]);

  useEffect(() => {
    if (agenciesIsError)
      openNotification({
        message: 'Error Getting Agencies',
        description: agenciesError.message,
      });
  }, [agenciesError?.message, agenciesIsError]);

  return (
    agencyinfo != null && (
      <ConfigurationLayout title={capAgyname}>
        <Card title="Definitions" loading={agencyInfoIsLoading}>
          <EditAgencySettings
            editFeaturePersistanceTSP={editFeaturePersistanceTSP}
            createFPResponse={editFeaturePersistanceTSPResponse}
            data={agencyinfo}
          />
          <EditAgency
            agency={agency || ''}
            agencies={agenciesList || []}
            editAgency={editAgency}
            response={editAgencyResponse}
          />
          <UploadStaticIntersections />
        </Card>
      </ConfigurationLayout>
    )
  );
};

const mapStateToProps = (state) => ({
  admin: state.user.admin,
});

export default connect(mapStateToProps, null)(withRouter(AgencyPage));
