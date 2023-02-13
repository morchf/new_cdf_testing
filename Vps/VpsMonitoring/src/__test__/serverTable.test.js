import React from 'react';
import ServerTable from '../serverTable';
import ConfirmModal from '../confirmModal';
import { mount } from 'enzyme';
import { BootstrapTable } from 'react-bootstrap-table';
import Button from 'react-bootstrap/Button';

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
    serverName: 'GLOBALINFRA2',
    vpsAvailability: 'INUSE',
  },
];

describe('has certain components', () => {
  let wrapper = mount(
    <ServerTable vpss={vpssExample} customerName="GLOBALINFRA" />
  );
  test('exists buttons and bootstrap table', () => {
    expect(wrapper.find(Button).at(0).text()).toEqual('Delete');
    expect(wrapper.find(Button).at(1).text()).toEqual('Stop');
    expect(wrapper.find(Button).at(2).text()).toEqual('Restart');
    expect(wrapper.find(Button).at(3).text()).toEqual('Start');
    expect(wrapper.containsMatchingElement(BootstrapTable)).toEqual(true);
  });
});

describe('state updates when click buttons with a row in subtable selected or not', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(
      <ServerTable vpss={vpssExample} customerName="GLOBALINFRA" />
    );
  });

  test('initial state of selected is null', () => {
    expect(wrapper.state().selected).toEqual([]);
  });

  test('click delete button when no row is selected, state and modal will be updated', () => {
    // click no row
    let button = wrapper.find('#Delete').first();
    button.simulate('click');
    expect(wrapper.state().buttonName).toEqual('Delete');
    expect(wrapper.state().selected).toEqual([]);
  });

  test('click a row and the state.selected will add its vps id', () => {
    // click a randon row with vps id = 'V764MM0283', state is updated
    let firstTd = wrapper.find('tr').at(4).find('td').at(1);
    firstTd.simulate('click');
    expect(firstTd.text()).toEqual('V764MM0283');
    wrapper.update();
    expect(wrapper.state().selected).toEqual(['V764MM0283']);

    // click again the randon row with vps id = 'V764MM0283', state is reupdated
    firstTd.simulate('click');
    wrapper.update();
    expect(wrapper.state().selected).toEqual([]);
  });

  test('click delete button when one row is selected', () => {
    // click a randon row with vps id = 'V764MM0283', state is updated
    let firstTd = wrapper.find('tr').at(4).find('td').at(1);
    firstTd.simulate('click');
    expect(firstTd.text()).toEqual('V764MM0283');
    wrapper.update();

    // before click 'delete' button, confirmModal doesn't appear
    let confirmModal = wrapper.find(ConfirmModal);
    expect(confirmModal.instance().state.showButtonModal).toEqual(false);
    let button = wrapper.find('#Delete').first();
    button.simulate('click');
    wrapper.update();

    // after clicking, states of ServerTable and ConfirmModal both updated
    expect(wrapper.state()).toEqual({
      buttonName: 'Delete',
      selected: ['V764MM0283'],
    });
    expect(confirmModal.instance().state.showButtonModal).toEqual(true);
  });
});
