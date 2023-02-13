import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQuery, mockQuery } from '../../../redux/utils/client';
import getStatusData, {
  getIntersectionListData,
  getIntersectionsMapData,
  getVehiclesData,
} from '../data';

const api = createApi({
  reducerPath: 'api/healthMonitoring',
  baseQuery,
  // Used to invalidate intersections data
  tagTypes: ['INTERSECTIONS'],
  endpoints: (builder) => ({
    getStatus: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Intersections Status',
          query: getStatusData,
        }),
    }),

    getIntersectionsMap: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Intersections Map',
          query: getIntersectionsMapData,
        }),
    }),

    getIntersectionsList: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Intersections List',
          query: getIntersectionListData,
        }),
      providesTags: ['INTERSECTIONS'],
    }),

    // Forces refetch of any queries with 'INTERSECTIONS' tag
    refreshIntersections: builder.mutation({
      queryFn: () => ({ data: null }),
      invalidatesTags: ['INTERSECTIONS'],
    }),

    getVehicles: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Vehicles Data',
          query: getVehiclesData,
        }),
    }),
  }),
});

export const {
  useGetStatusQuery,
  useGetIntersectionsMapQuery,
  useGetIntersectionsListQuery,
  useRefreshIntersectionsMutation,
  useGetVehiclesQuery,
} = api;

export const { resetApiState } = api.util;

export default api;
