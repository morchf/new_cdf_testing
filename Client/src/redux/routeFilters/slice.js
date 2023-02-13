/* eslint-disable no-param-reassign */
import { createSlice } from '@reduxjs/toolkit';
import { MONTH_AGO, TODAY } from '../../common/constants';
import { Direction, Timeframe } from '../../common/enums';

const initialState = {
  dateRange: {
    startDate: MONTH_AGO,
    endDate: TODAY,
  },
  direction: Direction.Inbound,
  periods: [Timeframe.PeakAM],
  availability: {
    scheduleDeviation: {
      min: null,
      max: null,
    },
    travelTime: {
      min: null,
      max: null,
    },
  },
};

const routeFilters = createSlice({
  name: 'routeFilters',
  initialState,
  reducers: {
    setDateRange: (state, { payload }) => {
      state.dateRange = payload;
    },
    setDirection: (state, { payload }) => {
      state.direction = payload;
    },
    setPeriods: (state, { payload }) => {
      state.periods = Array.isArray(payload) ? payload : [payload];
    },
  },
});

export const { setDateRange, setDirection, setPeriods } = routeFilters.actions;

export default routeFilters.reducer;
