import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Timeframe } from '../enums';
import { useGetAgencyInfoQuery } from '../../features/featurePersistence/api';
import { selectAgencyGuid } from '../../features/userAuth/store/selectors';
import { selectTimeperiod } from '../../features/featurePersistence/store/selectors';
import { PERIODS } from '../constants';
import { getPeakValues } from '../utils';

const useAgencyDefaults = () => {
  const agencyGuid = useSelector(selectAgencyGuid);
  const { isLoading: isTimeLoading } = useGetAgencyInfoQuery(agencyGuid);

  const timeperiod = useSelector(selectTimeperiod);
  const [agencyPeriods, setAgencyPeriods] = useState(PERIODS);
  useEffect(() => {
    if (!isTimeLoading && timeperiod.length === 2) {
      const { peakAM, peakPM } = getPeakValues(timeperiod[0], timeperiod[1]);
      setAgencyPeriods([
        {
          label: `Peak AM (${peakAM})`,
          value: Timeframe.PeakAM,
        },
        {
          label: `Peak PM (${peakPM})`,
          value: Timeframe.PeakPM,
        },
        {
          label: 'Off-Peak (not peak or weekends)',
          value: Timeframe.OffPeak,
        },
        {
          label: 'Weekends (Saturday & Sunday)',
          value: Timeframe.Weekends,
        },
        {
          label: 'All',
          value: Timeframe.All,
        },
      ]);
    }
  }, [isTimeLoading, timeperiod]);
  return { agencyGuid, agencyPeriods };
};

export default useAgencyDefaults;
