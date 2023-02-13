import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  timeperiod: [
    { start_time: '06:00:00', label: 'peak_am', end_time: '09:00:00' },
    { start_time: '16:00:00', label: 'peak_pm', end_time: '19:00:00' },
  ],
  onTimeRange: [-5, 2],
};

const featurePersistence = createSlice({
  name: 'featurePersistence',
  initialState,
  reducers: {
    setTimeperiod: (state, { payload }) => {
      state.timeperiod = payload;
    },
    setOnTimeRange: (state, { payload }) => {
      state.onTimeRange = payload;
    },
  },
});
export const { setTimeperiod, setOnTimeRange } = featurePersistence.actions;
export default featurePersistence.reducer;
