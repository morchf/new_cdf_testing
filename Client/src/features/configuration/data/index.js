import { wait } from '../../../common/utils';
import * as intersectionsData from './mockDataIntersections.json';
import * as vehiclesData from './mockDataVehicles.json';
import * as devicesData from './mockDataDevices.json';
import * as intersectionData from './mockDataIntersection.json';

export const getIntersectionsData = async (_token, _params) =>
  wait(2000).then(() => intersectionsData?.default);

export const getVehiclesConfigData = async (_token, _params) =>
  wait(2000).then(() => vehiclesData?.default);

export const getUnassignedDevicesData = async (_token, _params) =>
  wait(2000).then(() => devicesData?.default);

export const getIntersectionData = async (_token, _params) =>
  wait(2000).then(() => intersectionData?.default);
