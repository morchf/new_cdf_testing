/* eslint-disable no-param-reassign */
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  /* Route */
  vpss: {},
  csv: {},
  agency: {},
  vehicle: {},
  device: {},
  intersection: {},
  intersections: [],
};

const configuration = createSlice({
  name: 'configuration',
  initialState,
  reducers: {
    setVPSs: (state, { payload }) => {
      state.vpss = payload;
    },
    setCSV: (state, { payload }) => {
      state.csv = payload;
    },
    setAgency: (state, { payload }) => {
      state.agency = payload;
    },
    setVehicle: (state, { payload }) => {
      state.vehicle = payload;
    },
    setDevice: (state, { payload }) => {
      state.device = payload;
    },
    setIntersection: (state, { payload }) => {
      state.intersection = payload;
    },
    setIntersections: (state, { payload }) => {
      state.intersections = payload;
    },
  },
});

export const {
  setVPSs,
  setCSV,
  setAgency,
  setVehicle,
  setDevice,
  setIntersections,
  setIntersection,
} = configuration.actions;
export default configuration.reducer;

export const fetchVPSS = () => (dispatch) => {
  dispatch(setVPSs());
};
