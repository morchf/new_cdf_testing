import { wait } from '../../../common/utils';
import * as mapData from './mockDataMap.json';
import * as listData from './mockDataList.json';
import * as vehiclesData from './mockDataVehicles.json';

const statusData = {
  normal: 220,
  warning: 25,
  error: 95,
};

const firmwareHistogramData = [
  {
    Intersection: 'Shadeland Ave',
    version: '9.10',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '9.03',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '9.03',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '8',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '8.1',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '8.7',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '9.10',
  },
  {
    Intersection: 'Shadeland Ave',
    version: '9.10',
  },
];

const getStatusData = async (_token, _params) =>
  wait(2000).then(() => statusData);

export const getFirmwareHistogramData = async (_token, _params) =>
  wait(2000).then(() => firmwareHistogramData);

export const getIntersectionsMapData = async (_token, _params) =>
  wait(2000).then(() => mapData?.default);

export const getIntersectionListData = async (_token, _params) =>
  wait(2000).then(() => listData?.default);

export const getVehiclesData = async (_token, _params) =>
  wait(2000).then(() => vehiclesData?.default);

export default getStatusData;
