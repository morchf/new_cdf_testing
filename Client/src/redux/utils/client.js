import axios from 'axios';
import { Auth } from 'aws-amplify';
import { logSuccess, logError } from './apiLogger';

export const baseQuery = async (config, { dispatch, getState }) => {
  const { url, headers: configHeaders, data, ...rest } = config;
  const headers = { ...configHeaders } || {};

  try {
    // Add authorization, if available
    if ((await Auth.currentSession()).isValid()) {
      // TODO - change authorizers to use access tokens: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html
      headers.authorization = `${
        (await Auth.currentSession()).idToken.jwtToken
      }`;
    }
  } catch (error) {
    // TODO - handle any potential errors, lack of a current session, etc
  }
  const params = { ...config.params };

  // Add agency, region, and agency ID, if available
  const { agency, region, agencyGuid } = getState()?.user
    ? getState()?.user
    : {};
  if (agency) {
    params.agency = agency.toLowerCase();
  }
  if (region) {
    params.region = region.toLowerCase();
  }

  if (agencyGuid) {
    params.agencyId = agencyGuid;
  }
  // TODO: Need to add agency ID to store

  // Change agency into demo agency if it is pilot environment
  if (process.env.REACT_APP_SC_DOMAIN_NAME === 'cdfmanager-pilot') {
    params.agency = 'demo';
  }
  // Default headers
  if (!headers['content-type'] && !headers['Content-Type']) {
    headers['content-type'] = 'application/json';
  }

  if (!(data instanceof FormData)) JSON.stringify(data);

  return axios({
    ...config,
    url,
    params,
    data,
    headers,
  })
    .then((response) => {
      logSuccess(dispatch, response);
      return response;
    })
    .catch(({ response }) => {
      logError(dispatch, response);
      const message = response.data.message
        ? response.data.message
        : response.data;
      return { error: { message, ...rest } };
    });
};

export const mockQuery = (config) => {
  const { query, transformResponse, ...rest } = config;
  return query()
    .then((data) => {
      if (transformResponse) {
        return { data: transformResponse(data) };
      }
      return { data };
    })
    .catch(({ message }) => ({ error: { message, ...rest } }));
};
