import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Modal, Tabs, Form, Input, Select, Row, Col } from 'antd';
import Button from '../../../../common/components/Button';
import openNotification from '../../../../common/components/notification';
import { Make, Model } from '../../../../common/enums';
import skeletonRelation from '../../../../templates/skeleton_relation.json';
import { generateMakeOptions } from '../../utils';
import './style.css';

const { TabPane } = Tabs;

const Pane = {
  VEHICLE: 'vehicle',
  DEVICE: 'device',
};

const VehicleAssignmentModal = ({
  visible,
  onResponseChange,
  onCancel,
  vehiclesList,
  device,
  editDevice,
  associateDeviceResponse,
  associateDevice,
}) => {
  const [deviceMake, setDeviceMake] = useState(device.make);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [creatingNewVehicle, setCreatingVehicle] = useState(false);
  const [deviceForm] = Form.useForm();
  const { data, isLoading, isSuccess, isError } = associateDeviceResponse;

  const { region } = useSelector(({ user }) => user);
  const { agency } = useSelector(({ configuration }) => configuration);

  useEffect(() => {
    setSelectedVehicle(null);
  }, [visible]);

  useEffect(() => {
    deviceForm.setFieldsValue({
      deviceId: device?.deviceId,
      description: device?.description,
      gttSerial: device?.attributes?.gttSerial,
      serial: device?.attributes?.serial,
      addressMAC: device?.attributes?.addressMAC,
      addressLAN: device?.attributes?.addressLAN,
      addressWAN: device?.attributes?.addressWAN,
      IMEI: device?.attributes?.IMEI,
      make: device?.attributes?.make,
      model: device?.attributes?.model,
    });
    setDeviceMake(device?.attributes?.make);
  }, [deviceForm, device]);

  useEffect(() => {
    if (isSuccess) {
      onResponseChange();
      openNotification({
        message: 'Success!',
        description: data,
        type: 'success',
      });
    }
  }, [onResponseChange, data, isSuccess]);

  useEffect(() => {
    if (isError) {
      onResponseChange();
      openNotification({
        message: 'Error Associating Device to Vehicle',
        description: associateDeviceResponse.error.message,
      });
    }
  }, [onResponseChange, associateDeviceResponse.error?.message, isError]);

  const onSave = (e) => {
    if (!selectedVehicle) {
      openNotification({
        message:
          'Please select a vehicle before attempting to associate a device',
        description: '',
      });
    } else {
      try {
        /**
         * @TODO Add functionality to save vehicle edits from this modal
         */
        if (deviceForm.isFieldsTouched()) {
          const body = { ...device };
          const attributes = { ...device.attributes };
          const formValues = deviceForm.getFieldsValue();

          if (formValues.description !== '') {
            body.description = formValues.description;
          }
          if (formValues.gttSerial !== '') {
            attributes.gttSerial = formValues.gttSerial;
          }
          if (formValues.serial !== '') {
            attributes.serial = formValues.serial;
          }
          if (
            formValues.addressMAC !== '' &&
            formValues.make === Make.SierraWireless
          ) {
            attributes.addressMAC = formValues.addressMAC;
          } else if (formValues.make === Make.GTT) {
            attributes.addressMAC = '';
          }
          if (formValues.IMEI !== '') {
            if (
              formValues.make === Make.SierraWireless ||
              formValues.make === Make.Cradlepoint
            )
              attributes.IMEI = formValues.IMEI;
          } else attributes.IMEI = '';
          if (formValues.addressLAN !== '') {
            attributes.addressLAN = formValues.addressLAN;
          }
          if (formValues.addressWAN !== '') {
            attributes.addressWAN = formValues.addressWAN;
          }
          if (formValues.make !== '') {
            attributes.make = formValues.make;
          }
          if (
            formValues.make === Make.GTT &&
            device.attributes.model === Make.MP70
          ) {
            attributes.model = Model.Model2101;
          } else if (formValues.make === Make.GTT) {
            attributes.model = formValues.model;
          } else if (formValues.make === Make.SierraWireless) {
            attributes.model = Model.MP70;
          }

          body.attributes = { ...attributes };
          body.groups = {
            out: { ownedby: [`/${region}/${agency.attributes.name}`] },
          };

          delete body.direction;
          delete body.relation;

          editDevice(body);
        }

        e.preventDefault();
        const selected = [device.deviceId];
        const vehicleName = selectedVehicle.deviceId;
        const relation = {
          ...skeletonRelation,
          selected,
          vehicleName,
        };
        associateDevice(relation);
      } catch (err) {
        openNotification({
          message: 'Error associating device',
          description: err,
        });
      }
    }
  };

  const handleSelect = (deviceId) => {
    setSelectedVehicle(vehiclesList[deviceId]);
  };

  const generateSelectOptions = (range) => {
    const selectOptions = [];
    for (let i = 1; i < range + 1; i++) {
      selectOptions.push(
        <Select.Option key={i} value={i}>
          {i}
        </Select.Option>
      );
    }
    return selectOptions;
  };

  return (
    <Modal
      className="device-assignment-modal"
      okText={'Assign'}
      onOk={onSave}
      onCancel={onCancel}
      visible={visible}
      destroyOnClose={true}
      confirmLoading={isLoading}
    >
      <h2 className="h2-centered">Vehicle Assignment</h2>
      <Tabs>
        <TabPane tab="Vehicle Settings" key={Pane.VEHICLE}>
          {selectedVehicle === null && !creatingNewVehicle && (
            <div style={{ height: '415px' }}>
              <h2 className="h2-centered">Selection Options</h2>
              <p style={{ textAlign: 'center', margin: 0, marginBottom: '5%' }}>
                <span style={{ color: 'darkgrey' }}>
                  Pick a vehicle or create a new one
                </span>
              </p>
              <Select
                defaultValue="Existing Agency Vehicle"
                style={{
                  marginLeft: '28%',
                  marginRight: '28%',
                  width: '44%',
                }}
                onSelect={(values) => handleSelect(values)}
              >
                {Object.values(vehiclesList)?.map((vehicle) => (
                  <Select.Option
                    key={vehicle.deviceId}
                    value={vehicle.deviceId}
                  >
                    {vehicle.attributes.name}
                  </Select.Option>
                ))}
              </Select>
              <p className="or">OR</p>
              <Button
                disabled
                className="assign-device-button"
                type="primary"
                onClick={() => setCreatingVehicle(true)}
              >
                Create New Vehicle
              </Button>
            </div>
          )}
          {selectedVehicle && (
            <Form
              className="vehicle-assignment-modal-form-general"
              layout="vertical"
              initialValues={{
                name: selectedVehicle?.attributes?.name,
                description: selectedVehicle?.description,
                type: selectedVehicle?.attributes?.type,
                VID: selectedVehicle?.attributes?.VID,
                class: selectedVehicle?.attributes?.class,
                priority: selectedVehicle?.attributes?.priority,
                // preemptionLicense:
                //   selectedVehicle.preemptionLicense === 'active',
              }}
            >
              <Form.Item
                name="name"
                label="Vehicle Name"
                style={{ width: '45%' }}
              >
                <Input disabled />
              </Form.Item>
              <Form.Item
                name="type"
                label="Vehicle Type"
                style={{ width: '25%' }}
              >
                <Input disabled />
              </Form.Item>
              <Form.Item
                name="priority"
                label="Priority"
                style={{ width: '25%' }}
              >
                <Select disabled>
                  {agency.attributes.priority === 'High' ? (
                    <>
                      <Select.Option value="High">High</Select.Option>
                      <Select.Option value="Low">Low</Select.Option>
                    </>
                  ) : (
                    <Select.Option value="Low">Low</Select.Option>
                  )}
                </Select>
              </Form.Item>
              <Form.Item
                name="vehicleCode"
                label={
                  <span>
                    <span style={{ fontWeight: 'bold' }}>Vehicle Code </span>
                    &#40;agency:class:veh id, 1:1:3&#41;
                  </span>
                }
                style={{ display: 'inline-block' }}
              >
                <Input.Group size="large">
                  <Row gutter={8}>
                    <Col span={8}>
                      <Form.Item
                        className="vehicle-code-inputs"
                        name="agency"
                        label="Agency"
                      >
                        <Select style={{ width: '80%' }} disabled>
                          <Select.Option>X</Select.Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        className="vehicle-code-inputs"
                        name="class"
                        label="Class"
                      >
                        <Select style={{ width: '80%' }} disabled>
                          {generateSelectOptions(10)}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        className="vehicle-code-inputs"
                        name="VID"
                        label="Vehicle ID"
                      >
                        <Select style={{ width: '80%' }} disabled>
                          {generateSelectOptions(9999)}
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                </Input.Group>
              </Form.Item>
              <Form.Item name="VID" label="Vehicle ID" style={{ width: '75%' }}>
                <Input disabled />
              </Form.Item>
              <Form.Item
                name="description"
                label="GTT Description"
                style={{ width: '75%' }}
              >
                <Input disabled />
              </Form.Item>
              {/* <Form.Item
                name="preemptionLicense"
                valuePropName="checked"
                className="preemption-switch"
                label={<p>Pre-emption</p>}
              >
                <Switch style={{ marginLeft: '20px' }} />
              </Form.Item> */}
            </Form>
          )}
        </TabPane>
        <TabPane tab="Device Settings" key={Pane.DEVICE}>
          {device && (
            <Form
              form={deviceForm}
              className="edit-device-modal-form"
              layout="vertical"
            >
              <Form.Item
                className="edit-device-modal-form-item"
                name="deviceId"
                label="Device ID"
                style={{ width: '40%' }}
              >
                <Input type="text" />
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="description"
                label="Description"
                style={{ width: '40%' }}
              >
                <Input type="text" />
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="make"
                label="Make"
                style={{ width: '52%' }}
              >
                <Select allowClear onChange={(value) => setDeviceMake(value)}>
                  {generateMakeOptions()}
                </Select>
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="model"
                label="Model"
                style={{ width: '25%' }}
              >
                <Select allowClear>
                  {deviceMake === Make.GTT ? (
                    <>
                      <Select.Option value="2100">2100</Select.Option>
                      <Select.Option value="2101">2101</Select.Option>
                    </>
                  ) : deviceMake === Make.SierraWireless ? (
                    <Select.Option value="MP-70">MP-70</Select.Option>
                  ) : deviceMake === Make.Cradlepoint ? (
                    <>
                      <Select.Option value="IBR900">IBR900</Select.Option>
                      <Select.Option value="IBR1700">IBR1700</Select.Option>
                      <Select.Option value="R1900">R1900</Select.Option>
                    </>
                  ) : (
                    <></>
                  )}
                </Select>
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="gttSerial"
                label="GTT Serial"
                style={{ width: '47%' }}
              >
                <Input type="text" />
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="serial"
                label="Device Serial"
                style={{ width: '47%' }}
              >
                <Input type="text" />
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="addressLAN"
                label="LAN"
                style={{ width: '47%' }}
              >
                <Input type="text" />
              </Form.Item>
              <Form.Item
                className="edit-device-modal-form-item"
                name="addressWAN"
                label="WAN"
                style={{ width: '47%' }}
              >
                <Input type="text" />
              </Form.Item>
              {(deviceMake === Make.SierraWireless ||
                deviceMake === Make.Cradlepoint) && (
                <>
                  <Form.Item
                    className="edit-device-modal-form-item"
                    name="addressMAC"
                    label="MAC"
                    style={{ width: '47%' }}
                  >
                    <Input type="text" />
                  </Form.Item>
                  <Form.Item
                    className="edit-device-modal-form-item"
                    name="IMEI"
                    label="IMEI"
                    style={{ width: '47%' }}
                  >
                    <Input type="text" />
                  </Form.Item>
                </>
              )}
            </Form>
          )}
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default VehicleAssignmentModal;
