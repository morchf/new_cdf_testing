import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, Input, Form, Col, Row, AutoComplete } from 'antd';
import Button from '../../../../common/components/Button';
import EditThresholdsModal from '../EditThresholdsModal';
import { mapDataToInitialValues } from '../../utils';
import { numericValidator } from '../../../../common/utils/validations';
import './style.css';

const channelMapping = { 0: 'A', 1: 'B', 2: 'C', 3: 'D' };
const { TabPane } = Tabs;
const channelNames = [
  { value: 'East Bound' },
  { value: 'North Bound' },
  { value: 'Northeast Bound' },
  { value: 'Northwest Bound' },
  { value: 'Not Used' },
  { value: 'South Bound' },
  { value: 'Southeast Bound' },
  { value: 'Southwest Bound' },
  { value: 'West Bound' },
];
const ThresholdsForm = ({
  formData,
  onFormDataChange,
  priority,
  resetToDefaults,
}) => {
  const [allChannelsData, setAllChannelsData] = useState([]);
  const [allChannelsClasses, setAllChannelsClasses] = useState([]);
  const [editing, setEditing] = useState(false);
  const [currentChannel, setCurrentChannel] = useState(0);

  const [form] = Form.useForm();

  useEffect(() => {
    const channelsData = [];
    const channelsClasses = {};

    formData.forEach((data, index) => {
      const { classes, ...channel } = data;
      channelsData[index] = channel;
      channelsClasses[index] = classes;
    });

    const initialValues = mapDataToInitialValues(channelsData);
    form.setFieldsValue(initialValues);
    setAllChannelsData(channelsData);
    setAllChannelsClasses(channelsClasses);
  }, [form, formData]);
  const handleFormDataChange = useCallback(
    (channels) => {
      const formValues = form.getFieldsValue();
      const channelsData = [];
      Object.entries(formValues).forEach((entry) => {
        const [key, value] = entry;
        const [index, output] = key.split('-');
        if (!(index in channelsData)) {
          channelsData[index] = {};
        }
        channelsData[index][output] = value;
      });
      channelsData.forEach((channel, index) => {
        channel.classes = channels[index];
      });

      onFormDataChange(channelsData);
    },
    [form, onFormDataChange]
  );

  const applyToAll = useCallback(() => {
    const formValues = form.getFieldsValue();

    // Load channel 'A' settings
    const lostSignalHold = formValues['0-lostSignalHold'];
    const maxCallTime = formValues['0-maxCallTime'];

    if (lostSignalHold === undefined || maxCallTime === undefined) return;
    const channelClasses = allChannelsClasses[0];
    const currentChannelsData = [...allChannelsData];

    const updatedChannelsData = currentChannelsData.map((data, index) => {
      const channel = { ...data };

      channel.maxCallTime = maxCallTime;
      channel.lostSignalHold = lostSignalHold;
      channel.classes = channelClasses;

      return channel;
    });

    onFormDataChange(updatedChannelsData);
  }, [allChannelsClasses, allChannelsData, form, onFormDataChange]);

  const handleClick = (index) => {
    setCurrentChannel(index);
    setEditing(true);
  };
  return (
    <>
      <Form
        form={form}
        className="thresholds-form"
        layout="vertical"
        onFieldsChange={() => handleFormDataChange(allChannelsClasses)}
      >
        <Row>
          {formData.map((data, index) => (
            <Col key={index} span={5}>
              <Form.Item
                name={`${index}-channelName`}
                label={<b>Channel Name</b>}
                rules={[
                  {
                    max: 40,
                    message: 'Channel name cannot exceed 40 characters',
                  },
                ]}
              >
                <AutoComplete options={channelNames} filterOption={true} />
              </Form.Item>
              <Form.Item name={`${index}-channel`} label="Channel">
                {channelMapping[index]}
              </Form.Item>
              <Form.Item
                name={`${index}-maxCallTime`}
                label="Max Call Times"
                rules={[
                  numericValidator({
                    min: 0,
                    max: 65535,
                    errorMessage:
                      'Max Call Times should be within 0 - 65535 seconds',
                  }),
                ]}
              >
                <Input />
              </Form.Item>
              <Form.Item
                name={`${index}-lostSignalHold`}
                label="Lost Signal Hold"
                rules={[
                  numericValidator({
                    min: 0,
                    max: 65535,
                    errorMessage:
                      'Lost Signal Hold should be within 0 - 65535 seconds',
                  }),
                ]}
              >
                <Input />
              </Form.Item>
              <Form.Item label="ETA & Distance">
                <Button
                  className="thresholds-button-edit"
                  onClick={() => handleClick(index)}
                >
                  Edit Thresholds
                </Button>
              </Form.Item>
            </Col>
          ))}
        </Row>
        <Row>
          <Col span={15}>
            <Button
              className="thresholds-button-submit"
              type="secondary"
              size="lg"
              onClick={() => applyToAll()}
            >
              Apply Channel A settings to all Channels (?)
            </Button>
            <Button type="danger" size="lg" onClick={() => resetToDefaults()}>
              Reset to Default
            </Button>
          </Col>
        </Row>
      </Form>
      <EditThresholdsModal
        showModal={editing}
        setShowModal={setEditing}
        channel={currentChannel}
        allChannelsClasses={allChannelsClasses}
        onAllChannelsClassesChange={(channels) =>
          handleFormDataChange(channels)
        }
        priorityLevel={priority}
      />
    </>
  );
};

const ApproachesThresholds = ({
  thresholdsData,
  onThresholdsChange,
  resetToDefaults,
}) => {
  const { lowPriority, highPriority } = thresholdsData;

  const handleLowPriorityThresholdsChange = (thresholds) => {
    onThresholdsChange({ ...thresholdsData, lowPriority: thresholds });
  };
  const handleHighPriorityThresholdsChange = (thresholds) => {
    onThresholdsChange({ ...thresholdsData, highPriority: thresholds });
  };

  return (
    <Tabs
      className="thresholds-tabs"
      tabBarStyle={{ backgroundColor: '#f1efef' }}
    >
      <TabPane tab="Low Priority" key="2.1">
        <ThresholdsForm
          formData={lowPriority}
          onFormDataChange={handleLowPriorityThresholdsChange}
          priority={'Low'}
          resetToDefaults={resetToDefaults}
        />
      </TabPane>
      <TabPane tab="High Priority" key="2.2">
        <ThresholdsForm
          formData={highPriority}
          onFormDataChange={handleHighPriorityThresholdsChange}
          priority={'High'}
          resetToDefaults={resetToDefaults}
        />
      </TabPane>
    </Tabs>
  );
};

export default ApproachesThresholds;
