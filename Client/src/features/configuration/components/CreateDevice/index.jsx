/* eslint-disable no-nested-ternary */
import React, { useEffect } from 'react';
import { Form as AntForm, Input as AntInput, Select as AntSelect } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import openNotification from '../../../../common/components/notification';
import { Make } from '../../../../common/enums';
import skeletonComm from '../../../../templates/skeleton_comm.json';
import { deviceSchema } from '../../schemas';
import './style.css';

const CreateDevice = ({
  visible,
  agencyGroupPath,
  vehicle,
  onResponseChange,
  onCancel,
  createDevice,
  response,
}) => {
  const { data, isLoading, isSuccess, isError, error } = response;

  useEffect(() => {
    if (isSuccess) {
      onResponseChange();
      openNotification({
        message: data,
        type: 'success',
      });
    }
  }, [data, isSuccess, onResponseChange]);

  useEffect(() => {
    if (isError) {
      onResponseChange();
      openNotification({
        message: 'Error Creating Device',
        description: error.message,
      });
    }
  }, [error?.message, isError, onResponseChange]);

  const onSubmit = async (values, { resetForm }) => {
    const attributes = { ...values };
    const skeleton = { ...skeletonComm };
    const skeletonAttributes = { ...skeleton.attributes };
    const groups = { ...skeleton.groups };

    skeleton.description = attributes.description;

    skeletonAttributes.gttSerial = attributes.gttSerial;
    skeletonAttributes.serial = attributes.serial;
    skeletonAttributes.addressMAC = attributes.addressMAC;
    skeletonAttributes.addressLAN = attributes.addressLAN;
    skeletonAttributes.addressWAN = attributes.addressWAN;
    skeletonAttributes.IMEI = attributes.IMEI;
    skeletonAttributes.make = attributes.make;
    skeletonAttributes.model = attributes.model;
    skeleton.deviceId = attributes.serial;

    skeleton.attributes = skeletonAttributes;

    groups.ownedby = JSON.parse(`["${agencyGroupPath}"]`);
    skeleton.groups = groups;
    skeleton.vehicle = vehicle;

    createDevice(skeleton);
  };

  return (
    <div className="Create">
      <FormModal
        className="create-device-modal"
        visible={visible}
        onSubmit={onSubmit}
        onCancel={onCancel}
        destroyOnClose={true}
        loading={isLoading}
        validationSchema={deviceSchema}
        validateOnChange={false}
        initialValues={{
          description: '',
          gttSerial: '',
          serial: '',
          addressMAC: '',
          addressLAN: '',
          addressWAN: '',
          IMEI: '',
          make: '',
          model: '',
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
            <h1 style={{ textAlign: 'center', margin: 0, marginBottom: '3%' }}>
              Create a New Device
            </h1>
            <AntForm
              className="create-device-modal-form"
              labelCol={{ span: 6 }}
              wrapperCol={{ span: 12 }}
              onSubmit={handleSubmit}
              onChange={handleChange}
              initialValues={{
                description: '',
                gttSerial: '',
                serial: '',
                addressMAC: '',
                addressLAN: '',
                addressWAN: '',
                IMEI: '',
                make: '',
                model: '',
              }}
            >
              <AntForm.Item label="Description" help={errors.description}>
                <AntInput
                  type="text"
                  name="description"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="GTT Serial" help={errors.gttSerial} required>
                <AntInput
                  type="text"
                  name="gttSerial"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="Serial" help={errors.serial} required>
                <AntInput
                  type="text"
                  name="serial"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item
                label="LAN Address"
                help={errors.addressLAN}
                required
              >
                <AntInput
                  type="text"
                  name="addressLAN"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item
                label="WAN Address"
                help={errors.addressWAN}
                required
              >
                <AntInput
                  type="text"
                  name="addressWAN"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="Make" help={errors.priority} required>
                <AntSelect
                  name="make"
                  disabled={isSubmitting}
                  onChange={(value) => setFieldValue('make', value)}
                  value={values.make}
                >
                  <AntSelect.Option value="GTT">GTT</AntSelect.Option>
                  <AntSelect.Option value="Sierra Wireless">
                    Sierra Wireless
                  </AntSelect.Option>
                  <AntSelect.Option value="Cradlepoint">
                    Cradlepoint
                  </AntSelect.Option>
                </AntSelect>
              </AntForm.Item>
              {values.make === Make.SierraWireless ? (
                <AntForm.Item label="Model" help={errors.model} required>
                  <AntSelect
                    name="model"
                    disabled={isSubmitting}
                    onChange={(value) => setFieldValue('model', value)}
                  >
                    <AntSelect.Option value="MP-70">MP-70</AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>
              ) : values.make === Make.GTT ? (
                <AntForm.Item label="Model" help={errors.model} required>
                  <AntSelect
                    name="model"
                    disabled={isSubmitting}
                    onChange={(value) => setFieldValue('model', value)}
                  >
                    <AntSelect.Option value="2100">2100</AntSelect.Option>
                    <AntSelect.Option value="2101">2101</AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>
              ) : values.make === Make.Cradlepoint ? (
                <AntForm.Item label="Model" help={errors.model} required>
                  <AntSelect
                    name="model"
                    disabled={isSubmitting}
                    onChange={(value) => setFieldValue('model', value)}
                  >
                    <AntSelect.Option value="IBR900">IBR900</AntSelect.Option>
                    <AntSelect.Option value="IBR1700">IBR1700</AntSelect.Option>
                    <AntSelect.Option value="R1900">R1900</AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>
              ) : (
                <AntForm.Item label="Model" help={errors.model} required>
                  <AntSelect
                    name="model"
                    disabled={isSubmitting}
                    onChange={(value) => setFieldValue('model', value)}
                  >
                    <AntSelect.Option value="Null"></AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>
              )}
              {(values.make === Make.SierraWireless ||
                values.make === Make.Cradlepoint) && (
                <div>
                  <AntForm.Item
                    label="MAC Address"
                    help={errors.addressMAC}
                    required
                  >
                    <AntInput
                      type="text"
                      name="addressMAC"
                      onChange={handleChange}
                      disabled={isSubmitting}
                    />
                  </AntForm.Item>
                  <AntForm.Item label="IMEI" help={errors.IMEI} required>
                    <AntInput
                      type="text"
                      name="IMEI"
                      onChange={handleChange}
                      disabled={isSubmitting}
                    />
                  </AntForm.Item>
                </div>
              )}
            </AntForm>
          </div>
        )}
      </FormModal>
    </div>
  );
};

export default CreateDevice;
