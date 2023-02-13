import { createSelector } from '@reduxjs/toolkit';

const selectTravelTime = ({ travelTime }) => travelTime;

export const selectSelectedRoutes = createSelector(
  selectTravelTime,
  ({ selectedRoutes }) => selectedRoutes
);

export const selectSelectedRoute = createSelector(
  selectTravelTime,
  ({ selectedRoutes }) =>
    selectedRoutes?.length ? selectedRoutes[0] : selectedRoutes
);
