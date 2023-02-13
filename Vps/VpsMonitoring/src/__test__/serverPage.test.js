import React from 'react';
import ServerPage from '../serverPage';
import ServerTable from '../serverTable';
import ImportCSV from '../importCSV';
import Provision from '../provision';
import { mount } from 'enzyme';

const vpssExample = [
  {
    GTTmac: 'CC:69:B0:09:01:1B',
    VPS: 'V764MM0283',
    customerName: 'GLOBALINFRA',
    deviceStatus: 'RESTART',
    markToDelete: 'YES',
    primaryKey: '224754297012507',
    serverName: 'GLOBALINFRA2',
    vpsAvailability: 'AVAILABLE',
  },
  {
    GTTmac: 'CC:69:B0:09:00:A9',
    VPS: 'V764MM0169',
    customerName: 'GLOBALINFRA',
    deviceStatus: 'ACTIVE',
    dockerFinished: '0001-01-01T00:00:00Z',
    dockerIP: '172.31.84.243',
    dockerPort: '2000',
    dockerStart: '2020-06-25T14:04:57.495931165Z',
    dockerStatus: 'running',
    lastCheck: '06-25-2020T14:04:57.514789',
    markToDelete: 'NO',
    primaryKey: '224754297012393',
    serverName: 'GLOBALINFRA1',
    vpsAvailability: 'INUSE',
  },
];

test('exists barcharts, ServerTable, ImportCSV and Provision', () => {
  const wrapper = mount(
    <ServerPage vpss={vpssExample} customerName="GLOBALINFRA2" />
  );

  expect(wrapper.containsMatchingElement(<ServerTable />)).toEqual(true);
  expect(wrapper.containsMatchingElement(<ImportCSV />)).toEqual(true);
  expect(wrapper.containsMatchingElement(<Provision />)).toEqual(true);
});
