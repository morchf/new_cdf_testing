import React, { useEffect, useState, useCallback } from 'react';
import { Tabs, Form, Col, Row, Select } from 'antd';
import Button from '../../../../common/components/Button';
import { mapDataToInitialValues } from '../../utils';
import './style.css';

const { TabPane } = Tabs;

const OUTPUT_TYPES = ['NTCIP 1211'];
const CHANNEL_NAMES = ['A', 'B', 'C', 'D'];

const OutputsForm = ({
  formData,
  priority,
  onFormDataChange,
  resetToDefaults,
}) => {
  const [channelsData, setChannelsData] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    const { type, channels } = formData || { channels: [] };

    setChannelsData(channels);

    const initialValues = mapDataToInitialValues(channels);
    initialValues.type = type || 'NTCIP 1211';

    form.setFieldsValue(initialValues);
  }, [form, formData]);

  const outputOptions = [];
  const numOutputs = priority === 'lowPriority' ? 6 : 225;

  for (let i = 1; i < numOutputs + 1; i++)
    outputOptions.push(
      <Select.Option value={i} key={i}>
        {i}
      </Select.Option>
    );

  const handleFormDataChange = useCallback(() => {
    const newOutputs = { type: '', channels: [] };
    const formValues = form.getFieldsValue();
    Object.entries(formValues).forEach((entry) => {
      const [key, value] = entry;
      if (key === 'type') newOutputs[key] = formValues[key];
      else {
        const index = key.slice(0, 1);
        const output = key.slice(2);

        if (!(index in newOutputs.channels)) {
          newOutputs.channels[index] = {};
        }

        newOutputs.channels[index][output] = value;
      }
    });

    onFormDataChange(newOutputs);
  }, [form, onFormDataChange]);

  return (
    <Form
      form={form}
      className="outputs-form"
      layout="vertical"
      onFieldsChange={(_, allFields) => handleFormDataChange(allFields)}
    >
      <Row>
        <Col span={12}>
          <Form.Item
            name="type"
            label={
              <p>
                <b>
                  {priority === 'lowPriority' ? 'Low' : 'High'} Priority Output
                  Type
                </b>{' '}
                (applies to all channels)
              </p>
            }
          >
            <Select>
              {OUTPUT_TYPES.map((type) => (
                <Select.Option key={type} value={type}>
                  {type}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>
      <Row>
        {channelsData.map((data, index) => (
          <Col key={index} span={3}>
            <Form.Item name={`${index}-channel`} label={<b>Channel</b>}>
              {CHANNEL_NAMES[index]}
            </Form.Item>
            <Form.Item name={`${index}-straight`} label="Straight">
              <Select>{outputOptions}</Select>
            </Form.Item>
            <Form.Item name={`${index}-left`} label="Left">
              <Select>{outputOptions}</Select>
            </Form.Item>
            <Form.Item name={`${index}-right`} label="Right">
              <Select>{outputOptions}</Select>
            </Form.Item>
          </Col>
        ))}
      </Row>
      <Row>
        <Col span={6}>
          <Button
            className="outputs-button"
            type="danger"
            size="lg"
            onClick={() => resetToDefaults()}
          >
            Reset to Default
          </Button>
        </Col>
      </Row>
    </Form>
  );
};

const ApproachesOutputs = ({
  outputsData,
  onOutputsChange,
  setApproachIsSaved,
  resetToDefaults,
}) => {
  const { lowPriority, highPriority } = outputsData;

  return (
    <Tabs className="outputs-tabs" tabBarStyle={{ backgroundColor: '#f1efef' }}>
      <TabPane tab="Low Priority" key="lowPriorityOutputs">
        <OutputsForm
          formData={lowPriority}
          onFormDataChange={(fd) =>
            onOutputsChange({ ...outputsData, lowPriority: fd })
          }
          priority="lowPriority"
          setApproachIsSaved={setApproachIsSaved}
          resetToDefaults={resetToDefaults}
        />
      </TabPane>
      <TabPane tab="High Priority" key="highPriorityOutputs">
        <OutputsForm
          formData={highPriority}
          onFormDataChange={(fd) =>
            onOutputsChange({ ...outputsData, highPriority: fd })
          }
          priority="highPriority"
          setApproachIsSaved={setApproachIsSaved}
          resetToDefaults={resetToDefaults}
        />
      </TabPane>
    </Tabs>
  );
};

export default ApproachesOutputs;
