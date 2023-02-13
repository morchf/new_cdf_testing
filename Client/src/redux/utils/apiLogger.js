import { log, error } from '../logger/slice';
import {
  VPS_URL,
  CMS_URL,
  UI_URL,
  BATCH_URL,
  LATENESS_URL,
} from '../../common/constants';

const API_LOG_TAG = 'API';

// Anything outside of 200 reponse means something didn't go entirely right
const isSuccess = (statusCode) => +statusCode >= 200 && +statusCode <= 299;

// Any 200-level response means the request didn't fail, but something could still be wrong
// Log this kind of error instead of displaying to user
const isFailure = (statusCode) => +statusCode < 200 || +statusCode >= 300;

/** @TODO Next step: add notification suppression */
// Use method and feature to determine if notifications are shown to user
// Example: CDF post/put/delete should be shown, CDF get should be suppressed
const shouldDisplayToUser = (statusCode) =>
  +statusCode >= 400 && +statusCode <= 499;

export const logSuccess = (dispatch, response) => {
  const { config, status: statusCode, statusText } = response;

  switch (config.url) {
    case VPS_URL: // CDF URL
    case CMS_URL: // API URL
    case UI_URL: // UI URL
    case BATCH_URL: // BATCH URL
    case LATENESS_URL: // LATENESS URL
    default: {
      dispatch(
        log({
          tags: [API_LOG_TAG],
          body: {
            type: config?.url,
            statusCode,
            title: '',
            message: statusText,
            success: isSuccess(statusCode),
            failure: isFailure(statusCode),
            displayToUser: shouldDisplayToUser(statusCode),
            suppress: false,
            response,
          },
        })
      );
    }
  }
};

export const logError = (dispatch, response) => {
  const { config, status: statusCode, statusText } = response;

  switch (config.url) {
    case VPS_URL: // CDF URL
    case CMS_URL: // API URL
    case UI_URL: // UI URL
    case BATCH_URL: // BATCH URL
    case LATENESS_URL: // LATENESS URL
    default: {
      dispatch(
        error({
          tags: [API_LOG_TAG],
          body: {
            type: config?.url,
            statusCode,
            title: '',
            message: statusText,
            success: isSuccess(statusCode),
            failure: isFailure(statusCode),
            displayToUser: shouldDisplayToUser(statusCode),
            suppress: false,
            response,
          },
        })
      );
    }
  }
};
