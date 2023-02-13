import { createApi } from '@reduxjs/toolkit/query/react';
import { LATENESS_URL } from '../../common/constants';
import { baseQuery } from '../utils/client';

const api = createApi({
  reducerPath: 'api/core',
  baseQuery,
  endpoints: (builder) => ({
    status: builder.query({
      query: () => ({
        url: `${LATENESS_URL}/metrics/status`,
        title: 'Agency Status',
        method: 'POST',
      }),
    }),
  }),
});

export const { useStatusQuery } = api;

export const { resetApiState } = api.util;

export default api;
