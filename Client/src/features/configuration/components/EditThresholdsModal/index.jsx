import React, { useState, useEffect } from 'react';
import { Form, Row, Col, Input, Checkbox } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import Button from '../../../../common/components/Button';
import { numericValidator } from '../../../../common/utils/validations';
import './style.css';

const LowPriorityFields = [
  '0: Not Used',
  '1. Regular Transit',
  '2. Express Transit',
  '3. Paratransit',
  '4. Light Rail',
  '5. Trolley',
  '6. Snow Plows',
  '7. Supervisor',
  '8. Pavement Marking',
  '9: Installer/Set-up',
  '10: Bus Rapid Transit',
  '11: Not Used',
  '12: Not Used',
  '13: Not Used',
  '14: Not Used',
  '15: Not Used',
];

const HighPriorityFields = [
  '0. Not Used',
  '1. Fire Rescue/EMT/Ambulance',
  '2. Engine/Pumper',
  '3. Ladder/Arial/Snorkel',
  '4. Brush',
  '5. Miscellaneous',
  '6. Fire Chief/Captain',
  '7. Supervisor',
  '8. Maintenance',
  '9. Installer/Set-up',
  '10. Police/Sheriff Cars',
  '11. Miscellaneous Police/Sheriff',
  '12. Police Chief/Supervisor',
  '13. Private Ambulance',
  '14. Not Used',
  '15. Base Station',
];

const EditThresholdsModal = ({
  showModal,
  setShowModal,
  channel,
  allChannelsClasses,
  onAllChannelsClassesChange,
  priorityLevel,
}) => {
  const classes =
    priorityLevel === 'Low' ? LowPriorityFields : HighPriorityFields;
  const [form] = Form.useForm();

  useEffect(() => {
    const initialValues = {};
    const channelClasses = allChannelsClasses[channel];

    for (let i = 0; i < classes.length; i++) {
      initialValues[`${i}-ETA*`] = !channelClasses ? 30 : channelClasses[i].eta;
      initialValues[`${i}-Distance*`] = !channelClasses
        ? 1000
        : channelClasses[i].distance;
      // initialValues[`${i}-Active`] = true;
    }

    form.setFieldsValue(initialValues);
  }, [allChannelsClasses, channel, classes, form]);

  const onOk = () => {
    const currentChannelClasses = [...allChannelsClasses[channel]];
    const newChannelClassValues = form.getFieldsValue();
    currentChannelClasses.forEach((_, index) => {
      const currentChannelClass = { ...currentChannelClasses[index] };

      currentChannelClass.eta = +newChannelClassValues[`${index}-ETA*`];
      currentChannelClass.distance =
        +newChannelClassValues[`${index}-Distance*`];

      currentChannelClasses[index] = currentChannelClass;
    });

    onAllChannelsClassesChange({
      ...allChannelsClasses,
      [channel]: currentChannelClasses,
    });
    setShowModal(false);
  };

  const applyToAll = () => {
    const allFields = form.getFieldsValue();

    for (let i = 1; i < Object.entries(allFields).length / 2; i++) {
      allFields[`${i}-ETA*`] = allFields[`${1}-ETA*`];
      allFields[`${i}-Distance*`] = allFields[`${1}-Distance*`];
      // allFields[`${i}-Active`] = allFields[`${0}-Active`];
    }

    form.setFieldsValue(allFields);
  };

  const title = (
    <p
      style={{ fontWeight: 700, fontSize: '20px' }}
    >{`${priorityLevel} Priority Thresholds (GPS)`}</p>
  );

  return (
    <>
      {showModal && (
        <FormModal
          className="edit-thresholds-modal"
          title={title}
          // onSubmit={}
          visible={showModal}
          onCancel={() => setShowModal(false)}
          loading={false}
          // validationSchema={}
          validateOnChange={false}
          footer={[
            <div key={'footer'}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  marginBottom: '5px',
                }}
              >
                <Button type="primary" onClick={() => onOk()}>
                  Ok
                </Button>
                <Button type="secondary" onClick={() => applyToAll()}>
                  Apply to All Fields*
                </Button>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p>
                  ETA should be in the range of 0 - 255 sec <br />
                  Distance should be in the range of 0 - 5000 ft <br />
                  * to save time, you can change the class 1 values for ETA and
                  <br /> Distance and then use Apply to All Fields to populate
                  the rest
                </p>
              </div>
            </div>,
          ]}
        >
          {({ values }) => (
            <>
              <Form form={form} layout="horizontal" initialValues={values}>
                <Row>
                  <Col span={11}>
                    <h4>Class: Name</h4>
                  </Col>
                  <Col span={5}>
                    <h4>ETA* (sec)</h4>
                  </Col>
                  <Col span={5}>
                    <h4>Distance* (ft)</h4>
                  </Col>
                  {/* <Col span={3} style={{ textAlign: 'center' }}>
                    <h4>Active</h4>
                  </Col> */}
                </Row>
                {classes.map((data, index) => (
                  <Row key={index} style={{ height: '42px' }}>
                    <Col span={11}>
                      <p>{data}</p>
                    </Col>
                    <Col span={5}>
                      <Form.Item
                        style={{
                          display: 'inline-block',
                          width: 'calc(100% - 8px)',
                        }}
                        name={`${index}-ETA*`}
                        rules={[
                          numericValidator({
                            min: 0,
                            max: 255,
                            errorMessage: 'ETA should be within 0 - 255',
                          }),
                        ]}
                      >
                        <Input style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={5}>
                      <Form.Item
                        style={{
                          display: 'inline-block',
                          width: 'calc(100% - 8px)',
                        }}
                        name={`${index}-Distance*`}
                        rules={[
                          numericValidator({
                            min: 0,
                            max: 5000,
                            errorMessage:
                              'Distance should be within 0 - 5000 ft',
                          }),
                        ]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item
                        style={{
                          width: 'calc(100% - 8px)',
                          margin: 'auto',
                        }}
                        // name={`${index}-Active`}
                        // valuePropName="checked"
                      >
                        <div
                          style={{
                            display: 'block',
                            marginLeft: 'auto',
                            marginRight: 'auto',
                            width: '30%',
                          }}
                        >
                          {/* <Checkbox
                          // onChange={onCheckboxChange}
                          // checked={values[`${index}-Active`]}
                          /> */}
                        </div>
                      </Form.Item>
                    </Col>
                  </Row>
                ))}
              </Form>
            </>
          )}
        </FormModal>
      )}
    </>
  );
};

export default EditThresholdsModal;
