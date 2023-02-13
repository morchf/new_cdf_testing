import { createApi } from '@reduxjs/toolkit/query/react';
import {
  UI_URL,
  VPS_URL,
  INTERSECTIONS_URL,
  WHELEN_URL,
} from '../../../common/constants';
import { baseQuery, mockQuery } from '../../../redux/utils/client';

const api = createApi({
  reducerPath: 'api/configuration',
  baseQuery,
  tagTypes: [
    'VPSS',
    'INTERSECTIONS',
    'INTERSECTION',
    'REGIONS',
    'REGION',
    'AGENCIES',
    'AGENCY',
    'VEHICLES',
    'VEHICLE',
    'DEVICES',
    'AVAILABLE_DEVICES',
    'ASSOCIATED_DEVICES',
    'DEVICE',
  ],
  endpoints: (builder) => ({
    /* Agency */
    getVPSS: builder.query({
      query: ({ agyname }) => ({
        url: VPS_URL,
        title: 'Server Table',
        method: 'GET',
        params: {
          customerName: agyname.toUpperCase(),
        },
      }),
      providesTags: ['VPSS'],
    }),

    editVPSS: builder.mutation({
      query: (data) => ({
        url: VPS_URL,
        title: 'Edit VPS',
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['VPSS'],
    }),

    createVPSS: builder.mutation({
      query: (data) => ({
        url: VPS_URL,
        title: 'Create VPS',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['VPSS'],
    }),

    // Forces refetch of any queries with 'VPSS' tag
    refreshVPSS: builder.mutation({
      queryFn: () => ({ data: null }),
      invalidatesTags: ['VPSS'],
    }),

    getIntersections: builder.query({
      query: () => ({
        url: `${INTERSECTIONS_URL}/intersections`,
        title: 'Intersections',
        method: 'GET',
      }),
      providesTags: ['INTERSECTIONS'],
    }),

    createIntersection: builder.mutation({
      query: ({ intersection }) => ({
        url: `${INTERSECTIONS_URL}/intersections`,
        title: 'Intersections',
        method: 'POST',
        data: intersection,
      }),
      invalidatesTags: ['INTERSECTIONS'],
    }),

    getIntersection: builder.query({
      query: ({ intersectionId }) => ({
        url: `${INTERSECTIONS_URL}/intersections/${intersectionId}`,
        title: 'Intersection',
        method: 'GET',
      }),
      providesTags: ['INTERSECTION'],
    }),

    updateIntersection: builder.mutation({
      query: ({ intersection }) => ({
        url: `${INTERSECTIONS_URL}/intersections/${intersection.intersectionId}`,
        title: 'Intersection',
        method: 'PUT',
        data: intersection,
      }),
      invalidatesTags: ['INTERSECTIONS', 'INTERSECTION'],
    }),

    refreshIntersection: builder.mutation({
      queryFn: () => ({}),
      invalidatesTags: ['INTERSECTION'],
    }),

    // CMS endpoint
    setCMS: builder.mutation({
      query: ({ data, headers }) => ({
        url: VPS_URL,
        title: 'CMS',
        method: 'POST',
        headers,
        data,
      }),
    }),

    // CSV endpoint
    getCSV: builder.mutation({
      query: ({ data, params, headers, URL }) => ({
        url: URL,
        title: 'CSV',
        method: 'POST',
        params,
        headers,
        data,
      }),
      invalidatesTags: [
        'REGIONS',
        'REGION',
        'AGENCIES',
        'AGENCY',
        'VEHICLES',
        'VEHICLE',
        'DEVICES',
        'AVAILABLE_DEVICES',
        'DEVICE',
        'INTERSECTIONS',
      ],
    }),

    // Region endpoints
    getRegions: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Regions',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['REGIONS'],
    }),

    getRegion: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Region',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['REGION'],
    }),

    editRegion: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Edit Region',
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['REGION', 'REGIONS'],
    }),

    createRegion: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Create Region',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['REGION', 'REGIONS'],
    }),

    deleteRegion: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Delete Region',
        method: 'DELETE',
        data,
      }),
      invalidatesTags: ['REGIONS', 'REGION'],
    }),

    // Agency endpoints
    getAgencies: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Agencies',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['AGENCIES'],
    }),

    getAgency: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Agency',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['AGENCY'],
    }),

    editAgency: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Edit Agency',
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['AGENCY', 'AGENCIES'],
    }),

    createAgency: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Create Agency',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['AGENCY', 'AGENCIES'],
    }),

    deleteAgency: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Delete Agency',
        method: 'DELETE',
        data,
      }),
      invalidatesTags: ['AGENCIES', 'AGENCY'],
    }),

    // Vehicle endpoints
    getVehicles: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Vehicles',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['VEHICLES'],
    }),

    getVehicle: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Vehicle',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['VEHICLE'],
    }),

    editVehicle: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Edit Vehicle',
        method: 'PUT',
        data,
      }),
      invalidatesTags: ['VEHICLE', 'VEHICLES'],
    }),

    createVehicle: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Create Vehicle',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['VEHICLE', 'VEHICLES'],
    }),

    deleteVehicle: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Delete Vehicle',
        method: 'DELETE',
        data,
      }),
      invalidatesTags: ['VEHICLES', 'VEHICLE'],
    }),

    // Device endpoints
    getDevices: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Devices',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['DEVICES', 'AVAILABLE_DEVICES', 'ASSOCIATED_DEVICES'],
    }),

    // TODO: update query to use singular API endpoint once CDF migration complete
    getAvailableDevices: builder.query({
      queryFn: async (agencyDevicesNames, _queryApi, _extraOptions, query) => {
        if (!agencyDevicesNames) return { data: [] };

        let availableDevices = await Promise.all(
          agencyDevicesNames.map(async (deviceName) => {
            const params = `/devices/${deviceName}`;
            const res = await query({
              url: UI_URL,
              title: 'Available Devices',
              method: 'GET',
              params: {
                0: params,
              },
            });
            const resJson = res.data;
            return resJson?.devices ? null : resJson;
          }, [])
        );
        availableDevices = availableDevices.filter((x) => x);
        return { data: availableDevices };
      },
      providesTags: ['AVAILABLE_DEVICES'],
    }),

    // TODO: update query to use singular API endpoint once CDF migration complete
    getAssociatedDevices: builder.query({
      queryFn: async (vehicleIds, _queryApi, _extraOptions, query) => {
        if (!vehicleIds) return { data: {} };

        const associatedDevices = {};
        const associatedDevicesData = {};
        await Promise.all(
          vehicleIds.map(async (vehicleId) => {
            const params = `/devices/${vehicleId}/installedat/devices`;
            const res = await query({
              url: UI_URL,
              title: 'Associated Devices',
              method: 'GET',
              params: {
                0: params,
              },
            });
            const resJson = res.data;
            associatedDevices[vehicleId] = resJson.results;

            associatedDevicesData[vehicleId] = {
              devices: [],
              preemption: 'N/A',
            };
            resJson.results.forEach((device) => {
              const { make, model, integration, preemptionLicense } =
                device.attributes;
              const { preemption } = associatedDevicesData[vehicleId];
              if (
                !associatedDevicesData[vehicleId].devices.includes(make) &&
                make
              )
                associatedDevicesData[vehicleId].devices.push(make);
              if (
                !associatedDevicesData[vehicleId].devices.includes(model) &&
                model
              )
                associatedDevicesData[vehicleId].devices.push(model);
              if (
                !associatedDevicesData[vehicleId].devices.includes('Whelen') &&
                integration === 'Whelen'
              )
                associatedDevicesData[vehicleId].devices.push('Whelen');
              if (
                !associatedDevicesData[vehicleId].devices.includes(
                  'WhelenDevice'
                ) &&
                integration === 'Whelen'
              )
                associatedDevicesData[vehicleId].devices.push('WhelenDevice');
              if (preemptionLicense)
                associatedDevicesData[vehicleId].preemption =
                  preemption === 'active' ? preemption : preemptionLicense;
            });
          }, [])
        );
        return {
          data: { associatedDevices, associatedDevicesData },
        };
      },
      providesTags: ['ASSOCIATED_DEVICES'],
    }),

    getDevice: builder.query({
      query: ({ params }) => ({
        url: UI_URL,
        title: 'Device',
        method: 'GET',
        params: {
          0: params,
        },
      }),
      providesTags: ['DEVICE'],
    }),

    editDevice: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Edit Device',
        method: 'PUT',
        data,
      }),
      invalidatesTags: [
        'DEVICE',
        'DEVICES',
        'AVAILABLE_DEVICES',
        'ASSOCIATED_DEVICES',
      ],
    }),

    createDevice: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Create Device',
        method: 'POST',
        data,
      }),
      invalidatesTags: [
        'DEVICE',
        'DEVICES',
        'AVAILABLE_DEVICES',
        'ASSOCIATED_DEVICES',
      ],
    }),

    deleteDevice: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Delete Device',
        method: 'DELETE',
        data,
      }),
      invalidatesTags: ['DEVICE', 'DEVICES', 'ASSOCIATED_DEVICES'],
    }),

    dissociateDevice: builder.mutation({
      query: (data) => ({
        url: UI_URL,
        title: 'Dissociate Device',
        method: 'DELETE',
        data,
      }),
      invalidatesTags: [
        'DEVICE',
        'DEVICES',
        'AVAILABLE_DEVICES',
        'ASSOCIATED_DEVICES',
      ],
    }),

    /**
     * Intersection Endpoints
     */
    uploadStaticIntersections: builder.mutation({
      query: ({ data, regionName, agencyName }) => ({
        url: `${INTERSECTIONS_URL}/import`,
        title: 'Static Intersections',
        method: 'POST',
        params: { regionName, agencyName },
        headers: {
          'Content-Type': 'multipart/form-data',
          Accept: 'multipart/form-data',
        },
        data,
      }),
    }),

    /**
     * Whelen Change Preemption Endpoint
     */
    changePreemption: builder.mutation({
      query: ({ body }) => ({
        url: `${WHELEN_URL}/changepreemption`,
        title: 'Change Preemption',
        method: 'POST',
        data: body,
      }),
    }),
  }),
});

export const {
  useGetVPSSQuery,
  useEditVPSSMutation,
  useCreateVPSSMutation,
  useRefreshVPSSMutation,

  useGetIntersectionsQuery,
  useGetIntersectionQuery,
  useCreateIntersectionMutation,
  useUpdateIntersectionMutation,
  useRefreshIntersectionMutation,

  useSetCMSMutation,
  useGetCSVMutation,

  useGetRegionsQuery,
  useGetRegionQuery,
  useEditRegionMutation,
  useCreateRegionMutation,
  useDeleteRegionMutation,

  useGetAgenciesQuery,
  useGetAgencyQuery,
  useEditAgencyMutation,
  useCreateAgencyMutation,
  useDeleteAgencyMutation,

  useGetVehiclesQuery,
  useGetVehicleQuery,
  useEditVehicleMutation,
  useCreateVehicleMutation,
  useDeleteVehicleMutation,

  useGetDevicesQuery,
  useGetAvailableDevicesQuery,
  useGetAssociatedDevicesQuery,
  useGetDeviceQuery,
  useEditDeviceMutation,
  useCreateDeviceMutation,
  useDeleteDeviceMutation,
  useDissociateDeviceMutation,

  // Intersections
  useUploadStaticIntersectionsMutation,

  // Whelen Preemption
  useChangePreemptionMutation,
} = api;

export const { resetApiState } = api.util;

export default api;
