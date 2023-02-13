import * as mockDataDeviationCategoryGraph from './mockDataDeviationCategoryGraph.json';
import * as mockDataStopsChart from './mockDataStopsChart.json';
import * as mockDataTimeframeChart from './mockDataTimeframeChart.json';
import * as mockDataAvgMetricsStop from './mockDataAvgMetricsStop.json';
import * as mockDataAvgMetricsRoute from './mockDataAvgMetricsRoute.json';
import * as mockDataOnTimeStopsChart from './mockDataOnTimeStopsChart.json';
import * as mockDataOnTimeTimeframeChart from './mockDataOnTimeTimeframeChart.json';
import { wait } from '../../../common/utils';

export const routesData = {
  routes: [
    {
      label: 'Route 1',
      value: '1',
      route: {
        start: {
          label: 'Wade Park Blvd',
          location: [-8764100, 4274130],
        },
        end: {
          label: 'Summerford Dr',
          location: [-8764235, 4273870],
        },
        points: [
          [-8764100, 4274130],
          [-8764186, 4274209],
          [-8764202, 4274212],
          [-8764215, 4274204],
          [-8764232, 4274184],
          [-8764232, 4274184],
          [-8764234, 4274177],
          [-8764330, 4274073],
          [-8764328, 4274060],
          [-8764270, 4274010],
          [-8764270, 4273955],
          [-8764235, 4273870],
        ],
        stops: [
          {
            label: 'Bus Stop 1',
            location: [-8764215, 4274204],
          },
          {
            label: 'Bus Stop 2',
            location: [-8764330, 4274073],
          },
        ],
      },
    },
  ],
};

export const latenessData = [
  {
    label: 'Peak AM',
    lat: -8764186,
    lon: 4274209,
    lateness: -3,
  },
  {
    label: 'Peak AM',
    lat: -8764100,
    lon: 4274130,
    lateness: -2,
  },
  {
    label: 'Peak PM',
    lat: -8764215,
    lon: 4274204,
    lateness: -2.4,
  },
  {
    label: 'Peak PM',
    lat: -8764186,
    lon: 4274209,
    lateness: -1.7,
  },
  {
    label: 'Off-Peak',
    lat: -8764186,
    lon: 4274209,
    lateness: 2.4,
  },
  {
    label: 'Off-Peak',
    lat: -8764186,
    lon: 4274209,
    lateness: 1.2,
  },
  {
    label: 'Weekends',
    lat: -8764186,
    lon: 4274209,
    lateness: -0.4,
  },
  {
    label: 'Weekends',
    lat: -8764186,
    lon: 4274209,
    lateness: 0.4,
  },
];

export const getChartData = (
  period,
  analyzedRoute,
  deviationDirection,
  dateRange,
  selectedPeriods = ['Peak', 'Peak 2', 'Off-Peak', 'Weekends']
) => {
  const data = [];

  selectedPeriods.forEach((route) => {
    for (let i = 0; i < 40; i += 5) {
      data.push({
        label: route,
        busStop: `${i}`,
        lateness: Math.round((Math.random() * (4 - -4) + -4) * 100) / 100,
      });
    }
  });

  return data;
};

export const getRouteData = (
  selectedRoutes,
  routeNames,
  deviationDirection,
  dateRange
) => {
  const routes = [];

  selectedRoutes.forEach((selectedRoute) => {
    const selectedRouteName = routeNames.filter(
      (item) => selectedRoute === item.route
    )[0];
    const selectedRouteData = selectedRouteName
      ? routesData.routes.map((item) => {
          if (selectedRouteName.route === item.value) {
            return {
              ...item,
              color: selectedRouteName.color,
            };
          }

          return null;
        })[0]
      : null;

    if (selectedRouteData) routes.push(selectedRouteData);
  });

  return { routes: [...routesData.routes, ...routes] };
};

export const getDeviationCategoryChartData = async (_token, _params) =>
  wait(2000).then(() => mockDataDeviationCategoryGraph?.default);

export const getDeviationStopsChartData = async (_token, _params) =>
  wait(2000).then(() => mockDataStopsChart?.default);

export const getDeviationTimeframeChartData = async (_token, _params) =>
  wait(2000).then(() => mockDataTimeframeChart?.default);

export const getAvgMetricsStop = async () =>
  wait(2000).then(() => mockDataAvgMetricsStop?.default);

export const getAvgMetricsRoute = async () =>
  wait(2000).then(() => mockDataAvgMetricsRoute?.default);

export const getOnTimePercentStopsChartData = async (_token, _params) =>
  wait(2000).then(() => mockDataOnTimeStopsChart?.default);

export const getOnTimePercentTimeframeChartData = async (_token, _params) =>
  wait(2000).then(() => mockDataOnTimeTimeframeChart?.default);

export const getDeviationTimeframeChartForStopsData = async (_token, _params) =>
  wait(2000).then(() => mockDataTimeframeChart?.default);
export const getOnTimePercentTimeframeChartForStopsData = async (
  _token,
  _params
) => wait(2000).then(() => mockDataOnTimeTimeframeChart?.default);
