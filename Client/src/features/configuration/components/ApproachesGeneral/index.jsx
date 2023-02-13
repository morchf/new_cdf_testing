import React, { useEffect, useCallback } from 'react';
import { Form, Input, Select } from 'antd';

const TIME_ZONES = [
  'IDL',
  'UTC-11',
  'HDT',
  'HST',
  'MART',
  'AKST',
  'UTC-9',
  'PST',
  'UTC-8',
  'MST',
  'CST',
  'EAST',
  'EST',
  'AST',
  'NT',
  'BRT',
  'WGT',
  'UTC-2',
  'AZOT',
  'SST',
];

const ApproachesGeneral = ({ generalData, onGeneralDataChange }) => {
  const [form] = Form.useForm();

  const handleGeneralDataChange = useCallback(() => {
    onGeneralDataChange({
      ...generalData,
      ...form.getFieldsValue(),
    });
  }, [form, generalData, onGeneralDataChange]);

  useEffect(() => {
    form.setFieldsValue(generalData);
  }, [form, generalData]);

  return (
    <Form
      form={form}
      className="general-form"
      layout="vertical"
      onFieldsChange={handleGeneralDataChange}
    >
      <Form.Item
        name="intersectionName"
        label="Intersection Name"
        style={{ width: '40%' }}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="locationType"
        label="Location Type"
        style={{ width: 'calc(30% - 8px)' }}
      >
        <Select  defaultValue="NTCIP">
          <Select.Option>NTCIP</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item
        name="latitude"
        label="Latitude"
        style={{ display: 'inline-block', width: 'calc(15% - 8px)' }}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="longitude"
        label="Longitude"
        style={{
          display: 'inline-block',
          width: 'calc(15% - 8px)',
          margin: '0 8px',
        }}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="timezone"
        label="Time Zone"
        style={{ width: 'calc(30% - 8px)' }}
      >
        <Select>
          {TIME_ZONES.map((timezone) => (
            <Select.Option value={timezone} key={timezone}>
              {timezone}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>
    </Form>
  );
};

export default ApproachesGeneral;
