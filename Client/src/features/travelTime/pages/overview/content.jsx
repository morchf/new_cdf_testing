import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import TravelTimeTable from '../../components/TravelTimeTable';
import PerformanceSummary from '../../components/PerformanceSummary';
import openNotification from '../../../../common/components/notification';
import useOverview from '../../hooks/useOverview';
import { ERROR_NOT_SETUP, ERROR_NO_DATA } from '../../../../common/constants';
import './style.css';
import useAgency from '../../../../common/hooks/useAgency';
import { Metric } from '../../../../common/enums';
import useFeaturePersistence from '../../../featurePersistence/hooks/useFeaturePersistence';
import {
  setTimeperiod,
  setOnTimeRange,
} from '../../../featurePersistence/store/slice';
import { selectAgencyGuid } from '../../../userAuth/store/selectors';

const OverviewContent = () => {
  const agencyGuid = useSelector(selectAgencyGuid);
  const {
    agency: agencyData,
    isLoading: agencyLoading,
    isError: agencyConfigError,
    error: agencyInfoError,
  } = useFeaturePersistence();
  const dispatch = useDispatch();
  useEffect(() => {
    if (!agencyLoading && !agencyConfigError && 'Feature' in agencyData) {
      const timeperiodData = [
        {
          start_time: agencyData.Feature.peak_am_range.start_time,
          label: 'peak_am',
          end_time: agencyData.Feature.peak_am_range.end_time,
        },
        {
          start_time: agencyData.Feature.peak_pm_range.start_time,
          label: 'peak_pm',
          end_time: agencyData.Feature.peak_pm_range.end_time,
        },
      ];
      const onTimeData = [
        agencyData.Feature.late_schedule_deviation_limit,
        agencyData.Feature.early_schedule_deviation_limit,
      ];
      dispatch(setTimeperiod(timeperiodData));
      dispatch(setOnTimeRange(onTimeData));
    }
  }, [agencyLoading, agencyData, dispatch, agencyConfigError]);

  const { performance, table, isLoading } = useOverview();
  const {
    status: { availability },
    isLoading: isStatusLoading,
  } = useAgency();

  // Check if any date range is available
  useEffect(() => {
    if (isStatusLoading || availability[Metric.TravelTime].isAvailable) {
      return;
    }

    openNotification({
      message: 'Error 404',
      description: ERROR_NOT_SETUP,
    });
  }, [availability, isStatusLoading]);

  // Check if any data is available in date range
  useEffect(() => {
    if (
      table &&
      table.length === 0 &&
      !isLoading &&
      availability[Metric.TravelTime].isAvailable
    ) {
      openNotification({
        message: 'Error 404',
        description: ERROR_NO_DATA,
      });
    }
  }, [table, isLoading, availability]);
  return (
    <div className="overview-content">
      <PerformanceSummary
        isLoading={isLoading}
        performance={performance}
        routes={table}
      />
      <div className="overview-content__table">
        <TravelTimeTable dataSource={table} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default OverviewContent;
