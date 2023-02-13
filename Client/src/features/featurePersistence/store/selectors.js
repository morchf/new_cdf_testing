import { createSelector } from '@reduxjs/toolkit';

const selectFeaturePersistence = ({ featurePersistence }) => featurePersistence;

export const selectTimeperiod = createSelector(
  selectFeaturePersistence,
  ({ timeperiod }) => timeperiod
);

export const selectTimeRange = createSelector(
  selectFeaturePersistence,
  ({ onTimeRange }) => onTimeRange
);
