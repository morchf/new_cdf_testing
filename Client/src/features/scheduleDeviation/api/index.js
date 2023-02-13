import { createApi } from '@reduxjs/toolkit/query/react';
import { LATENESS_URL } from '../../../common/constants';
import { PEAKS_DEFIINITION, Timeframe, Direction } from '../../../common/enums';
import { reduceSegments } from '../../../common/utils';
import { baseQuery, mockQuery } from '../../../redux/utils/client';
import {
  getAvgMetricsStop,
  getDeviationStopsChartData,
  getDeviationTimeframeChartForStopsData,
  getOnTimePercentTimeframeChartData,
  getOnTimePercentTimeframeChartForStopsData,
} from '../data';
import { transformColumnChartData } from '../utils';
import { addMinutesToMetrics, formatTimeframePoints } from './utils';

const PERIOD = 'month';

const api = createApi({
  reducerPath: 'api/scheduleDeviation',
  baseQuery,
  endpoints: (builder) => ({
    /* Agency */
    getRoutesTable: builder.query({
      query: ({
        dateRange: { startDate, endDate },
        direction,
        periods,
        onTimeRange,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/lateness/agg_lateness_reduction`,
        title: 'Table Data',
        method: 'POST',
        data: {
          // ToDo: Pass actual agency's on-time range when available
          on_time_range: onTimeRange,
          selected_direction:
            direction === Direction.All
              ? [Direction.Inbound, Direction.Outbound]
              : [direction],
          selected_timeperiod:
            periods[0] === Timeframe.All
              ? [
                  Timeframe.PeakAM,
                  Timeframe.PeakPM,
                  Timeframe.OffPeak,
                  Timeframe.Weekends,
                ]
              : periods,
          timeperiod,
        },
        params: {
          start_date: startDate,
          end_date: endDate,
          period: PERIOD,
        },
      }),
    }),

    /* Route */

    getLatenessPoints: builder.query({
      query: ({
        routeName,
        dateRange: { startDate, endDate },
        direction,
        periods,
        onTimeRange,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/lateness/agg_lateness_per_route`,
        title: 'Lateness Points Data',
        method: 'POST',
        data: {
          on_time_range: onTimeRange,
          selected_direction:
            direction === Direction.All
              ? [Direction.Inbound, Direction.Outbound]
              : [direction],
          selected_timeperiod:
            periods[0] === Timeframe.All
              ? [
                  Timeframe.PeakAM,
                  Timeframe.PeakPM,
                  Timeframe.OffPeak,
                  Timeframe.Weekends,
                ]
              : periods,
          timeperiod,
        },
        params: {
          start_date: startDate,
          end_date: endDate,
          route: routeName,
          period: PERIOD,
        },
      }),
      transformResponse: addMinutesToMetrics,
    }),

    getLatenessRoutes: builder.query({
      query: ({ routeName, dateRange: { endDate }, direction }) => ({
        url: `${LATENESS_URL}/routes_map_data`,
        title: 'Lateness Routes Data',
        method: 'POST',
        data: {
          selected_direction:
            direction === Direction.All
              ? [Direction.Inbound, Direction.Outbound]
              : [direction],
        },
        params: {
          // Endpoint does not handle date range. TODAY returns most recent GTFS published version.
          start_date: endDate,
          end_date: endDate,
          route: routeName,
        },
      }),
      transformResponse: reduceSegments,
    }),

    getLatenessPerRouteTimeframe: builder.query({
      query: ({
        routeName,
        dateRange: { startDate, endDate },
        direction,
        periods,
        period,
        onTimeRange,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/lateness/agg_lateness_per_route_day`,
        title: 'Deviation / On-Time Percentage Chart',
        method: 'POST',
        data: {
          on_time_range: onTimeRange,
          selected_direction:
            direction === Direction.All
              ? [Direction.Inbound, Direction.Outbound]
              : [direction],
          selected_timeperiod:
            periods[0] === Timeframe.All
              ? [
                  Timeframe.PeakAM,
                  Timeframe.PeakPM,
                  Timeframe.OffPeak,
                  Timeframe.Weekends,
                ]
              : periods,
          timeperiod,
        },
        params: {
          start_date: startDate,
          end_date: endDate,
          route: routeName,
          period,
        },
      }),
      transformResponse: formatTimeframePoints,
    }),

    getDeviationStopsChart: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Deviation Stops Chart',
          query: getDeviationStopsChartData,
        }),
    }),

    /* Stop */

    getAvgMetricsStop: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Average Metrics Stop',
          query: getAvgMetricsStop,
        }),
    }),

    getDeviationTimeframeChartForStops: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'Deviation Timeframe Chart For Stops',
          query: getDeviationTimeframeChartForStopsData,
        }),
    }),

    getOnTimePercentTimeframeChartForStops: builder.query({
      queryFn: () =>
        mockQuery({
          title: 'On-Time Percentage Timeframe Chart For Stops',
          query: getOnTimePercentTimeframeChartForStopsData,
          transformResponse: (data) => transformColumnChartData(data, true),
        }),
    }),
  }),
});

export const {
  useGetRoutesTableQuery,

  useGetLatenessPointsQuery,
  useGetLatenessRoutesQuery,
  useGetDeviationStopsChartQuery,
  useGetLatenessPerRouteTimeframeQuery,

  useGetAvgMetricsStopQuery,
  useGetDeviationTimeframeChartForStopsQuery,
  useGetOnTimePercentTimeframeChartForStopsQuery,
} = api;

export const { resetApiState } = api.util;

export default api;
