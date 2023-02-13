import React from 'react';
import Provision from '../provision';
import { mount } from 'enzyme';
import { Button, Form, Col } from 'react-bootstrap';

describe('has certain components', () => {
  test('exists an input and Button', () => {
    const wrapper = mount(<Provision />);
    expect(wrapper.find('form')).toHaveLength(1);
  });
});

describe('should update state while the form changes', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(<Provision customerName="GLOBALINFRA" />);
  });

  test('should update device prefix while type in prefix', () => {
    expect(wrapper.state().devicePrefix).toEqual('');
    let devicePrefix = wrapper.find(Form.Control).at(0);
    devicePrefix.simulate('change', { target: { value: 'V764' } });
    wrapper.update();
    expect(wrapper.state().devicePrefix).toEqual('V764');
  });

  test('should update count while type in count', () => {
    expect(wrapper.state().count).toEqual('');
    let count = wrapper.find(Form.Control).at(1);
    count.simulate('change', { target: { value: 50 } });
    wrapper.update();
    expect(wrapper.state().count).toEqual(50);
  });
});
