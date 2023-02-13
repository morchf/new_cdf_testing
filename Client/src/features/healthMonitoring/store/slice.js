/* eslint-disable no-param-reassign */
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  filters: {},
};

const healthMonitoring = createSlice({
  name: 'healthMonitoring',
  initialState,
  reducers: {
    setFilters: (store, { payload }) => {
      store.filters = payload;
    },
  },
});

export const { setFilters } = healthMonitoring.actions;
export default healthMonitoring.reducer;
