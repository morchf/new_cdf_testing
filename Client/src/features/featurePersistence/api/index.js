import { createApi } from '@reduxjs/toolkit/query/react';
import CDF_URL, {
  FEATURE_PERSISTENCE_URL,
} from '../../../common/constants/apis';
import { baseQuery } from '../../../redux/utils/client';

export const api = createApi({
  reducerPath: 'api/featurePersistence',
  tagTypes: ['AGENCY_INFO'],
  baseQuery,
  endpoints: (builder) => ({
    /* Feature Persistence */
    getAgencyInfo: builder.query({
      query: (agencyGuid) => ({
        url: `${FEATURE_PERSISTENCE_URL}`,
        title: 'Get agency config',
        method: 'GET',
        params: {
          AgencyGUID: agencyGuid,
          FeatureName: 'tsp-analytics',
        },
      }),
      providesTags: ['AGENCY_INFO'],
    }),
    editFeaturePersistanceTSP: builder.mutation({
      query: (data) => ({
        url: `${FEATURE_PERSISTENCE_URL}`,
        title: 'Update Feature Persistance values for TSP Analytics',
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['AGENCY_INFO'],
    }),
  }),
});
export const { useGetAgencyInfoQuery, useEditFeaturePersistanceTSPMutation } =
  api;
export const { resetApiState } = api.util;
export default api;
