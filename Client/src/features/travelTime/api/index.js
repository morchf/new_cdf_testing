import { createApi } from '@reduxjs/toolkit/query/react';
import { LATENESS_URL,FEATURE_PERSISTENCE_URL } from '../../../common/constants';
import { PEAKS_DEFIINITION, Direction, Timeframe } from '../../../common/enums';
import { reduceSegments } from '../../../common/utils';
import { baseQuery } from '../../../redux/utils/client';
import {
  inferStopOrder,
  mergeIntersectionsWithMetrics,
  mergeSegmentsWithMetrics,
} from '../utils';
import { addMinutesToMetrics } from './utils';

const PERIOD = 'month';

const api = createApi({
  reducerPath: 'api/travelTime',
  baseQuery,
  endpoints: (builder) => ({
    /* Agency */
    getOverview: builder.query({
      query: ({ dateRange: { startDate, endDate }, direction, periods,timeperiod }) => ({
        url: `${LATENESS_URL}/metrics/travel_time/agg_travel_time`,
        title: 'Overview Page',
        method: 'POST',
        data: {
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

    getAvgMetrics: builder.query({
      query: ({
        routeName,
        dateRange: { startDate, endDate },
        direction,
        periods,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/travel_time/agg_travel_time_per_period`,
        title: 'Average Metrics',
        method: 'POST',
        data: {
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
          route: routeName,
        },
      }),
      // TODO: Remove conversion to minutes
      transformResponse: addMinutesToMetrics,
    }),

    getRouteSegments: builder.query({
      query: ({ routeName, direction, dateRange: { endDate } }) => ({
        url: `${LATENESS_URL}/routes_map_data`,
        title: 'Travel Time Map',
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
      transformResponse: (data) => {
        const points = reduceSegments(data);

        if (!points?.length || !points[0]?.segments) return points;

        // TODO: Move logic into API
        const segments = inferStopOrder(points[0].segments);

        return [{ ...points[0], segments }];
      },
    }),

    getSegmentMetrics: builder.query({
      query: ({
        routeName,
        dateRange: { startDate, endDate },
        direction,
        periods,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/travel_time/agg_travel_time_per_route`,
        title: 'Segment Metrics',
        method: 'POST',
        data: {
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
      transformResponse: (response) => {
        // TODO: Remove conversion to minutes
        const responseWithMinutes = addMinutesToMetrics(response);
        return mergeSegmentsWithMetrics(responseWithMinutes);
      },
    }),

    getChartMetrics: builder.query({
      query: ({
        routeName,
        dateRange: { startDate, endDate },
        direction,
        periods,
        period,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/travel_time/agg_travel_time_per_route_day`,
        title: 'Chart Metrics',
        method: 'POST',
        data: {
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
    }),

    getSignalDelay: builder.query({
      query: ({
        routeName,
        dateRange: { startDate, endDate },
        direction,
        periods,
        timeperiod,
      }) => ({
        url: `${LATENESS_URL}/metrics/travel_time/agg_signal_delay_per_route_intersection`,
        title: 'Signal Delay',
        method: 'POST',
        data: {
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
      transformResponse: mergeIntersectionsWithMetrics,
    }),

    getIntersections: builder.query({
      query: ({ routeName, direction, dateRange: { endDate } }) => ({
        url: `${LATENESS_URL}/metrics/travel_time/route_intersections`,
        title: 'Intersections',
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
      transformResponse: (response) =>
        // Fields: { direction, route, route_id, intersections }
        response.length ? response[0].intersections : response.intersections,
    }),
  }),
});

export const {
  useGetOverviewQuery,
  useGetAvgMetricsQuery,
  useGetRouteSegmentsQuery,
  useGetSegmentMetricsQuery,
  useGetChartMetricsQuery,
  useGetSignalDelayQuery,
  useGetIntersectionsQuery,
} = api;

export const { resetApiState } = api.util;

export default api;
