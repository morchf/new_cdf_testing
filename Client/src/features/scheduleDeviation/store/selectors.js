import { createSelector } from '@reduxjs/toolkit';

const selectScheduleDeviation = ({ scheduleDeviation }) => scheduleDeviation;

export const selectSelectedRoutes = createSelector(
  selectScheduleDeviation,
  ({ selectedRoutes }) => selectedRoutes
);

export const selectSelectedRoute = createSelector(
  selectScheduleDeviation,
  ({ selectedRoutes }) =>
    selectedRoutes?.length ? selectedRoutes[0] : selectedRoutes
);
