/* eslint-disable no-param-reassign */
import { createSlice } from '@reduxjs/toolkit';
import api from '../api';

const initialState = {
  /* Route */
  selectedRoutes: [],
  travelTimeSegments: [],
};

const travelTime = createSlice({
  name: 'travelTime',
  initialState,
  reducers: {
    setSelectedRoutes: (state, { payload }) => {
      state.selectedRoutes = payload;
    },
  },

  /* API */
  extraReducers: (builder) => {
    builder.addMatcher(
      api.endpoints.getRouteSegments.matchFulfilled,
      (state, { payload }) => {
        state.travelTimeSegments = payload;
      }
    );
  },
});

export const { setSelectedRoutes } = travelTime.actions;
export default travelTime.reducer;
