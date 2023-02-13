import { wait } from '../../../common/utils';
import routesData from './routesData';
import segmentsData from './segmentsData';

/** Travel Time mock data */

const avgMetricsData = {
  signalDelay: {
    change: 2.13,
    isBetter: true,
    mins: 18.47,
    percentage: 0.247,
  },
  dwellTime: {
    change: 1.01,
    isBetter: false,
    mins: 3.21,
    percentage: 0.043,
  },
  driveTime: {
    change: 5.01,
    isBetter: true,
    mins: 52.89,
    percentage: 0.716,
  },
  travelTime: {
    change: 6.13,
    isBetter: true,
    mins: 74.57,
    percentage: 1.0,
  },
};

const travelTimeChartData = [
  { period: '2021-02-18', value: Math.random() },
  { period: '2021-03-18', value: Math.random() },
  { period: '2021-04-18', value: Math.random() },
  { period: '2021-05-18', value: Math.random() },
  { period: '2021-06-18', value: Math.random() },
  { period: '2021-07-18', value: Math.random() },
];

const mapItemChartData = [
  { period: '2021-02-18', value: Math.random() },
  { period: '2021-03-18', value: Math.random() },
  { period: '2021-04-18', value: Math.random() },
  { period: '2021-05-18', value: Math.random() },
  { period: '2021-06-18', value: Math.random() },
  { period: '2021-07-18', value: Math.random() },
];

const performanceData = {
  top: {
    routes: ['1', '12', '14'],
    updDate: '2021-08-02',
  },
  worst: {
    routes: ['90', '91', '9R'],
    updDate: '2021-08-03',
  },
};

export const travelTimeTableData = [
  {
    route: '1',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '2',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '3',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '4',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '5',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '6',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '7',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '8',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '9',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '10',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '11',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '12',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '13',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '14',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '15',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '16',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '17',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '18',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '19',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
  {
    route: '20',
    avgTravelTime: '49.679',
    avgDriveTime: '27.115',
    avgTspSavings: '3.84',
    avgDwellTime: '7.844',
  },
];

const signalDelayData = [
  { intersection: '1st & 3rd', avgSignalDelay: '3.12', change: '0.253' },
  { intersection: 'Broadway', avgSignalDelay: '1.24', change: '0.25' },
  { intersection: '1st & 5th', avgSignalDelay: '4.16', change: '1.1' },
  { intersection: '42nd & 5th', avgSignalDelay: '1.17', change: '0' },
  { intersection: '42nd & 7th', avgSignalDelay: '3.94', change: '1' },
];

/** Travel Time API simulating methods */

export const getPerformanceSummary = async (_token, _params) => {
  const response = await wait(2000).then(() => performanceData);
  return response;
};

export const getTravelTimeTable = async (_token, _params) => {
  const response = await wait(2000).then(() => travelTimeTableData);
  return response;
};

export const getAvgMetrics = async (_token, _params) => {
  const response = await wait(2000).then(() => avgMetricsData);
  return response;
};

export const getTravelTimeChart = async (_token, _params) => {
  const response = await wait(2000).then(() => travelTimeChartData);
  return response;
};

export const getMapItemChart = async (_token, _params) => {
  const response = await wait(2000).then(() => mapItemChartData);
  return response;
};

export const getTravelTimeMap = async (_token, _params) => {
  const response = await wait(2000).then(() => routesData);
  return response;
};

export const getRouteSegments = async (_token, _params) => {
  const response = await wait(2000).then(() => segmentsData);
  return response;
};
