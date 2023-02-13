import { resetApiState as resetScheduleDeviationApiState } from '../../features/scheduleDeviation/api';
import { resetApiState as resetTravelTimeApiState } from '../../features/travelTime/api';
import { resetApiState as resetHealthMonitoringApiState } from '../../features/healthMonitoring/api';
import { resetApiState as resetConfigurationApiState } from '../../features/configuration/api';
import { resetApiState as resetCoreApiState } from '../api';
import { resetApiState as resetFeaturePersistenceApiState  } from "../../features/featurePersistence/api";

// Invalidate cached data and run action
export const resetApi =
  (action) =>
  (...rest) =>
  (dispatch) => {
    dispatch(resetFeaturePersistenceApiState());
    dispatch(resetScheduleDeviationApiState());
    dispatch(resetTravelTimeApiState());
    dispatch(resetHealthMonitoringApiState());
    dispatch(resetConfigurationApiState());
    dispatch(resetCoreApiState());
    dispatch(action(...rest));
  };
