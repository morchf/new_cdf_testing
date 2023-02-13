/* eslint-disable no-param-reassign */
import { createSlice } from '@reduxjs/toolkit';
import { Metric } from '../../../common/enums';
import api from '../api';

const initialState = {
  /* Meta */
  filters: {},
  // ToDo: Use an actual data when the range will be configured at the agency level.

  /* Route */
  selectedMetric: Metric.OnTimePercentage,
  selectedRoutes: [],
  latenessPoints: [],
  latenessRoutes: [],
};

const scheduleDeviation = createSlice({
  name: 'scheduleDeviation',
  initialState,
  reducers: {
    setFilters: (state, { payload }) => {
      state.filters = payload;
    },
    setSelectedMetric: (state, { payload }) => {
      state.selectedMetric = payload;
    },
    setSelectedRoutes: (state, { payload }) => {
      state.selectedRoutes = payload;
    },
  },

  /* API */

  extraReducers: (builder) => {
    builder.addMatcher(
      api.endpoints.getLatenessRoutes.matchFulfilled,
      (state, { payload }) => {
        // Save response from 'getLatenessRoutes' query to store
        state.latenessRoutes = payload;
      }
    );

    builder.addMatcher(
      api.endpoints.getLatenessPoints.matchFulfilled,
      (state, { payload }) => {
        // Save response from 'getLatenessPoints' query to store
        state.latenessPoints = payload;
      }
    );
  },
});

export const { setSelectedRoutes, setFilters, setSelectedMetric } =
  scheduleDeviation.actions;
export default scheduleDeviation.reducer;
