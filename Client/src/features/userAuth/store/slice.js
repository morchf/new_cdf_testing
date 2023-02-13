/* eslint-disable no-param-reassign */
import { createSlice } from '@reduxjs/toolkit';
import { resetApi } from '../../../redux/utils/api';
import { accessLocalStorage } from '../../../common/utils';

const { storeLocalItem, getLocalItem } = accessLocalStorage();

const initialState = {
  loading: false,
  idToken: null,
  error: '',
  admin: false,
  region: '',
  agency: '',
  agencyGuid: localStorage.getItem('user/agencyGuid'),
};

const user = createSlice({
  name: 'user',
  initialState,
  reducers: {
    loginUserRequest: (state) => {
      state.loading = true;
    },
    loginUserSuccess: (state, { payload }) => {
      // const isAdmin = payload['custom:admin'] ?? false;
      // const region = !isAdmin ? payload['custom:region'] : getLocalItem('user/region');
      // const agency = !isAdmin ? payload['custom:agency'] : getLocalItem('user/agency');

      const isAdmin =
        payload['cognito:groups']?.length &&
        payload['cognito:groups'][0].includes('Admin');

      let [region, agency] = [
        getLocalItem('user/region') ?? '',
        getLocalItem('user/agency') ?? '',
      ];
      if (payload['cognito:groups']?.length && !isAdmin) {
        [region, agency] = payload['cognito:groups'][0].split('_');
        storeLocalItem('user/region', region);
        storeLocalItem('user/agency', agency);
      }

      let agencyGuid = getLocalItem('user/agencyGuid') ?? '';

      if (!isAdmin) {
        agencyGuid = payload['custom:agencyGUID'];
        storeLocalItem('user/agencyGuid', agencyGuid);
      }

      return {
        ...state,
        idToken: payload,
        admin: isAdmin,
        region,
        agency,
        agencyGuid,
      };
    },
    logoutUserRequest: (state) => ({
      ...state,
      loading: true,
    }),
    logoutUserSuccess: (state) => {
      localStorage.clear();
      return {
        ...state,
        loading: false,
        idToken: null,
        error: '',
        admin: false,
        region: '',
        agency: '',
        agencyGuid: '',
      };
    },
    authUserFailure: (state, { payload }) => ({
      ...state,
      loading: false,
      idToken: null,
      error: payload,
      admin: false,
      region: '',
      agency: '',
      agencyGuid: '',
    }),
    setAdminRegion: (state, { payload }) => {
      storeLocalItem('user/region', payload);
      state.region = payload;
    },
    setAdminAgency: (state, { payload }) => {
      storeLocalItem('user/agency', payload.name);
      storeLocalItem('user/agencyGuid', payload.agencyGuid);
      state.agency = payload.name;
      state.agencyGuid = payload.agencyGuid;
    },
  },
});

export const authUserFailure = resetApi(user.actions.authUserFailure);
export const setAdminRegion = resetApi(user.actions.setAdminRegion);
export const setAdminAgency = resetApi(user.actions.setAdminAgency);
export const logoutUserSuccess = resetApi(user.actions.logoutUserSuccess);

export const { loginUserSuccess, loginUserRequest, logoutUserRequest } =
  user.actions;

export default user.reducer;
