import { createSlice } from '@reduxjs/toolkit';

const LogLevel = {
  INFO: 'INFO',
  ERROR: 'ERROR',
};

const MAX_NUM_LOGS = 10;

const initialState = {
  logs: [],
  latestLog: null,
  errors: [],
  latestError: null,
};

const logger = createSlice({
  name: 'logger',
  initialState,
  reducers: {
    log: (state, { payload: { tags, body } }) => {
      state.logs.unshift({
        type: LogLevel.INFO,
        tags,
        body,
      });
      state.latestLog = {
        type: LogLevel.INFO,
        tags,
        body,
      };
      if (state.logs.length >= MAX_NUM_LOGS) state.logs.length = MAX_NUM_LOGS;
    },
    error: (state, { payload: { body, tags = [] } }) => {
      state.logs.unshift({
        type: LogLevel.ERROR,
        tags,
        body,
      });
      state.errors.unshift({
        type: LogLevel.ERROR,
        tags,
        body,
      });
      state.latestError = {
        type: LogLevel.ERROR,
        tags,
        body,
      };
      if (state.logs.length >= MAX_NUM_LOGS) state.logs.length = MAX_NUM_LOGS;
      if (state.logs.errors >= MAX_NUM_LOGS) state.logs.errors = MAX_NUM_LOGS;
    },
  },
});

export const { log, error } = logger.actions;

export default logger.reducer;
