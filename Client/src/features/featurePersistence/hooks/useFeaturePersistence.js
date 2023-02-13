import { useCallback } from 'react';
import { useSelector } from 'react-redux';
import { selectAgencyGuid } from '../../userAuth/store/selectors';
import { selectTimeperiod, selectTimeRange } from '../store/selectors';
import {
  useEditFeaturePersistanceTSPMutation,
  useGetAgencyInfoQuery,
} from '../api';

// Returns list of all Devices
const useFeaturePersistence = () => {
  const agencyGuid = useSelector(selectAgencyGuid);

  const {
    data: agency,
    isLoading,
    isError,
    error,
  } = useGetAgencyInfoQuery(agencyGuid);

  const timeperiod = useSelector(selectTimeperiod);
  const onTimeRange = useSelector(selectTimeRange);
  const [lateBand, earlyBand] = onTimeRange;
  const skeleton = {};
  skeleton.FeatureName = 'tsp-analytics';
  skeleton.AgencyGUID = agencyGuid;
  const skeletonAttributes = { ...skeleton.Feature };
  const peakPmRange = {};
  const peakAmRange = {};
  peakAmRange.start_time = timeperiod[0].start_time;
  peakAmRange.end_time = timeperiod[0].end_time;
  peakPmRange.start_time = timeperiod[1].start_time;
  peakPmRange.end_time = timeperiod[1].end_time;
  skeletonAttributes.early_schedule_deviation_limit = earlyBand;
  skeletonAttributes.late_schedule_deviation_limit = lateBand;
  skeletonAttributes.peak_pm_range = peakPmRange;
  skeletonAttributes.peak_am_range = peakAmRange;
  skeleton.Feature = skeletonAttributes;

  const [editFP, editFeaturePersistanceTSPResponse] =
    useEditFeaturePersistanceTSPMutation();

  // Invalidates Device cache upon Device creation
  const editFeaturePersistanceTSP = useCallback(
    (data) => {
      editFP(data);
    },
    [editFP]
  );
  return {
    agency: agency ?? skeleton,
    isLoading,
    isError,
    error,
    editFeaturePersistanceTSPResponse,
    editFeaturePersistanceTSP,
  };
};

export default useFeaturePersistence;
