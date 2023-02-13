import { combineReducers } from '@reduxjs/toolkit';

import scheduleDeviationApi from '../features/scheduleDeviation/api';
import scheduleDeviation from '../features/scheduleDeviation/store/slice';
import travelTimeApi from '../features/travelTime/api';
import travelTime from '../features/travelTime/store/slice';
import healthMonitoringApi from '../features/healthMonitoring/api';
import healthMonitoring from '../features/healthMonitoring/store/slice';
import configurationApi from '../features/configuration/api';
import coreApi from './api';
import configuration from '../features/configuration/store/slice';
import featurePersistenceApi from '../features/featurePersistence/api';
import featurePersistence from '../features/featurePersistence/store/slice';
import user from '../features/userAuth/store/slice';
import routeFilters from './routeFilters/slice';

import logger from './logger/slice';

const rootReducer = () =>
  combineReducers({
    // Feature Persistence
    [featurePersistenceApi.reducerPath]: featurePersistenceApi.reducer, featurePersistence,
    // Schedule Deviation
    [scheduleDeviationApi.reducerPath]: scheduleDeviationApi.reducer,
    scheduleDeviation,

    // Travel Time
    [travelTimeApi.reducerPath]: travelTimeApi.reducer,
    travelTime,

    // Health Monitoring
    [healthMonitoringApi.reducerPath]: healthMonitoringApi.reducer,
    healthMonitoring,

    // Devices & VPS Configuration
    [configurationApi.reducerPath]: configurationApi.reducer,
    configuration,

    // Core
    [coreApi.reducerPath]: coreApi.reducer,

    // Meta
    routeFilters,

    // Session
    user,

    // Logger
    logger,
  });

export default rootReducer;
