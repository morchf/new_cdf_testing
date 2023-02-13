import React from 'react';
import App from '../App';
import SearchBar from '../SearchBar';
import CustomerPage from '../customerPage';
import { mount, shallow } from 'enzyme';
jest.mock('../fetchData');

describe('has certain components', () => {
  test('exists <SearchBar> and <CustomerPage>', () => {
    const wrapper = mount(<App />);
    expect(wrapper.containsMatchingElement(<SearchBar />)).toEqual(true);
    expect(wrapper.containsMatchingElement(<CustomerPage />)).toEqual(true);
  });
});

test('mocks fetching vps data from api and update the vpss state', (done) => {
  const wrapper = shallow(<App />);
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

  setTimeout(() => {
    wrapper.update();
    const state = wrapper.instance().state;

    expect(state.vpss).toEqual(vpssExample);
    done();
  });
});
