/* eslint-disable no-underscore-dangle */
import { configureStore, isRejectedWithValue } from '@reduxjs/toolkit';

import openNotification from '../common/components/notification';
import { errorHandler } from '../common/utils';

import scheduleDeviationApi from '../features/scheduleDeviation/api';
import travelTimeApi from '../features/travelTime/api';
import healthMonitoringApi from '../features/healthMonitoring/api';
import configurationApi from '../features/configuration/api';
import coreApi from './api';
import rootReducer from './rootReducer';
import featurePersistenceApi from '../features/featurePersistence/api'

const initialState = {};

export const rtkQueryErrorLogger = () => (next) => (action) => {
  if (isRejectedWithValue(action)) {
    const { message: description, title } = action?.payload;
    const message = `Error - ${title}`;

    // Display error to user and log

    /** @TODO_ryan_kinnucan implement openNotificaions with issue TSPA-1010 once error logic is defined  */
    // openNotification({ message, description });
    errorHandler(title, description);
  }

  return next(action);
};

export default configureStore({
  preloadedState: initialState,
  reducer: rootReducer(),
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      immutableCheck: false,
      serializableCheck: false,
    }).concat([
      // API
      rtkQueryErrorLogger,
      scheduleDeviationApi.middleware,
      travelTimeApi.middleware,
      healthMonitoringApi.middleware,
      configurationApi.middleware,
      coreApi.middleware,
      featurePersistenceApi.middleware,
    ]),
});
