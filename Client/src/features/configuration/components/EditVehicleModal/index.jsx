import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import {
  Form as AntForm,
  Input as AntInput,
  Select,
  Switch,
  Row,
  Col,
} from 'antd';
import FormModal from '../../../../common/components/FormModal';
import openNotification from '../../../../common/components/notification';
import { useChangePreemptionMutation } from '../../api';
import { editVehicleSchema } from '../../schemas';
import './style.css';

const EditVehicleModal = ({
  vehicle,
  associatedDevices,
  preemption,
  editVehicle,
  editVehicleResponse,
  visible,
  onResponseChange,
  onCancel,
}) => {
  const [preemptionActive, setPreemptionActive] = useState(false);
  const [preemptionChanged, setPreemptionChanged] = useState(false);
  const { data, isLoading, isSuccess, isError, error } = editVehicleResponse;
  const [changePreemption, changePreemptionResponse] =
    useChangePreemptionMutation();

  const { region } = useSelector(({ user }) => user);
  const { agency } = useSelector(({ configuration }) => configuration);

  useEffect(() => {
    setPreemptionActive(preemption === 'active');
  }, [preemption]);

  useEffect(() => {
    if (isSuccess) {
      onResponseChange();
      openNotification({
        message: data,
        type: 'success',
      });
    }
  }, [onResponseChange, data, isSuccess]);

  useEffect(() => {
    if (isError) {
      onResponseChange();
      openNotification({
        message: 'Error Editing Vehicle',
        description: error.message,
      });
    }
  }, [onResponseChange, error?.message, isError]);

  const handlePreemptionToggle = (checked) => {
    setPreemptionChanged(true);
    setPreemptionActive(checked);
  };

  const onSubmit = async (values) => {
    const body = { ...vehicle };
    const attributes = { ...body.attributes };
    Object.keys(attributes).forEach((key, value) => {
      if (Object.prototype.hasOwnProperty.call(values, key)) {
        if (key === 'class' || key === 'VID')
          attributes[key] = parseInt(values[key], 10);
        else attributes[key] = values[key];
      }
    });
    body.attributes = { ...attributes };
    if (values.name !== '') {
      body.attributes.name = values.name;
    }
    if (values.description !== '') {
      body.description = values.description;
    }
    delete body.direction;
    delete body.relation;
    body.groups = {
      out: { ownedby: [`/${region}/${agency.name.toLowerCase()}`] },
    };
    editVehicle(body);

    if (preemptionChanged) {
      const devices = {};
      associatedDevices.forEach((device) => {
        if ('preemptionLicense' in device.attributes)
          devices[`${device.deviceId}`] = preemptionActive
            ? 'active'
            : 'inactive';
      });

      const body = {
        agency_guid: agency.attributes.agencyID,
        devices,
      };

      changePreemption({ body });
    }
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
    <FormModal
      className="edit-vehicle-modal"
      okText={'Save'}
      onSubmit={onSubmit}
      visible={visible}
      onCancel={onCancel}
      validationSchema={editVehicleSchema}
      validateOnChange={false}
      destroyOnClose={true}
      loading={isLoading}
      initialValues={{
        name: vehicle?.attributes?.name,
        description: vehicle?.description,
        type: vehicle?.attributes?.type,
        VID: vehicle?.attributes?.VID,
        class: vehicle?.attributes?.class,
        priority: vehicle?.attributes?.priority,
      }}
    >
      {({
        handleSubmit,
        handleChange,
        values,
        errors,
        isSubmitting,
        setFieldValue,
      }) => (
        <div>
          <h1 style={{ textAlign: 'center', margin: 0, marginBottom: '1%' }}>
            Vehicle {vehicle.name} Settings
          </h1>
          <AntForm
            className="edit-vehicle-modal-form"
            layout="vertical"
            onSubmit={handleSubmit}
            onChange={handleChange}
          >
            <AntForm.Item
              label="Vehicle Name"
              help={errors.name}
              style={{ width: '45%' }}
            >
              <AntInput
                type="text"
                name="name"
                value={values.name}
                onChange={handleChange}
              />
            </AntForm.Item>
            <AntForm.Item
              label="Vehicle Type"
              help={errors.type}
              style={{ width: '25%' }}
            >
              <AntInput
                type="text"
                name="type"
                value={values.type}
                onChange={handleChange}
              />
            </AntForm.Item>
            <AntForm.Item
              label="Priority"
              help={errors.priority}
              style={{ width: '25%' }}
            >
              <Select
                name="priority"
                onChange={(value) => setFieldValue('priority', value)}
                defaultValue={values.priority}
              >
                {agency.attributes.priority === 'High' ? (
                  <>
                    <Select.Option value="High">High</Select.Option>
                    <Select.Option value="Low">Low</Select.Option>
                  </>
                ) : (
                  <Select.Option value="Low">Low</Select.Option>
                )}
              </Select>
            </AntForm.Item>
            <AntForm.Item
              label={
                <span>
                  <span style={{ fontWeight: 'bold' }}>Vehicle Code </span>
                  &#40;agency:class:veh id, 1:1:3&#41;
                </span>
              }
              style={{ display: 'inline-block' }}
            >
              <AntInput.Group size="large">
                <Row gutter={8}>
                  <Col span={8}>
                    <AntForm.Item
                      className="vehicle-code-inputs"
                      label="Agency"
                    >
                      <Select
                        style={{ width: '80%' }}
                        disabled
                        name="agency"
                        value={values.agency}
                      >
                        <Select.Option value="X">X</Select.Option>
                      </Select>
                    </AntForm.Item>
                  </Col>
                  <Col span={8}>
                    <AntForm.Item className="vehicle-code-inputs" label="Class">
                      <Select
                        style={{ width: '80%' }}
                        name="class"
                        value={values.class}
                        onChange={(value) => setFieldValue('class', value)}
                      >
                        {generateSelectOptions(10)}
                      </Select>
                    </AntForm.Item>
                  </Col>
                  <Col span={8}>
                    <AntForm.Item
                      className="vehicle-code-inputs"
                      label="Vehicle ID"
                    >
                      <Select
                        style={{ width: '80%' }}
                        name="VID"
                        value={values.VID}
                        onChange={(value) => setFieldValue('VID', value)}
                      >
                        {generateSelectOptions(9999)}
                      </Select>
                    </AntForm.Item>
                  </Col>
                </Row>
              </AntInput.Group>
            </AntForm.Item>
            <AntForm.Item
              label="VID"
              help={errors.VID}
              style={{ width: '75%' }}
            >
              <AntInput
                type="number"
                name="VID"
                value={values.VID}
                onChange={handleChange}
              />
            </AntForm.Item>
            <AntForm.Item
              label="GTT Description"
              help={errors.description}
              style={{ width: '75%' }}
            >
              <AntInput
                name="description"
                value={values.description}
                onChange={handleChange}
              />
            </AntForm.Item>
            {preemption === 'N/A' ? (
              <></>
            ) : (
              <AntForm.Item
                className="preemption-switch"
                label={<p>Pre-emption</p>}
              >
                <Switch
                  style={{ marginLeft: '20px' }}
                  onChange={(checked) => handlePreemptionToggle(checked)}
                  defaultChecked={preemption === 'active'}
                />
              </AntForm.Item>
            )}
          </AntForm>
        </div>
      )}
    </FormModal>
  );
};

export default EditVehicleModal;
