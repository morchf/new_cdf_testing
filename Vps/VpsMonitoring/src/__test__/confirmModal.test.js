import React from 'react';
import ConfirmModal from '../confirmModal';
import { mount } from 'enzyme';
import { Button, Modal } from 'react-bootstrap';
const axios = require('axios');
jest.mock('axios');

describe('has header, body, footer as expected', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(<ConfirmModal vpsName="V764MM0169" buttonName="Start" />);
    wrapper.setState({ showButtonModal: true });
  });

  test('shows header as Start File', () => {
    const header = wrapper.find(Modal.Header);
    expect(header.length).toEqual(1);
  });
  test('shows Body', () => {
    const body = wrapper.find(Modal.Body);
    expect(body.text()).toEqual('Are you sure you want to start the 10 VPS?');
  });
  test('shows Footer', () => {
    const footer = wrapper.find(Modal.Footer);
    expect(footer.text()).toEqual('CancelConfirm');
  });
});

describe('click buttons', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(<ConfirmModal vpsName="V764MM0169" buttonName="Start" />);
    wrapper.setState({ showButtonModal: true });
  });

  test('click cancel will close the confirmModal', () => {
    const cancalButton = wrapper.find(Button).first();
    expect(cancalButton.text()).toEqual('Cancel');
    cancalButton.simulate('click');
    expect(wrapper.state().showButtonModal).toEqual(false);
  });

  test('click confirm will open the responseModal', () => {
    expect(wrapper.state().showButtonModal).toEqual(true);
    expect(wrapper.state()).toEqual({
      response: '',
      showButtonModal: true,
      showErrorModal: false,
      showResponseModal: false,
    });
    const confirmButton = wrapper.find(Button).last();
    expect(confirmButton.text()).toEqual('Confirm');
  });
});
