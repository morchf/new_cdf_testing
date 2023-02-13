import React from 'react';
import ImportCSV from '../importCSV';
import { mount } from 'enzyme';
import { Button } from 'react-bootstrap';

describe('should upload binary file and update state', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(<ImportCSV />);
  });

  test('fileSelectedHandler to change importedCSV state', () => {
    expect(wrapper.state().importedCSV).toEqual(null);
    wrapper.find('input').simulate('change', {
      target: {
        files: ['dummyValue.csv'],
      },
    });
    wrapper.update();
    expect(wrapper.state().importedCSV).toEqual('dummyValue.csv');
  });
});
