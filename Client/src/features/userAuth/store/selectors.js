import { createSelector } from '@reduxjs/toolkit';

const selectUser = ({ user }) => user;

export const selectAgencyGuid = createSelector(
    selectUser,
    ({ agencyGuid }) => agencyGuid
  );