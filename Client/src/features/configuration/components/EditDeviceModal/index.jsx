import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Form as AntForm, Input as AntInput, Select as AntSelect } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import openNotification from '../../../../common/components/notification';
import { Make, Model } from '../../../../common/enums';
import { generateMakeOptions } from '../../utils';
import { editDeviceSchema } from '../../schemas';
import './style.css';

const EditDeviceModal = ({
  vehicle,
  device,
  visible,
  onResponseChange,
  onCancel,
  editDeviceResponse,
  editDevice,
}) => {
  const { data, isLoading, isSuccess, isError, error } = editDeviceResponse;

  const { region, agency } = useSelector(({ user }) => user);

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
        message: 'Error Editing Device',
        description: error.message,
      });
    }
  }, [onResponseChange, error?.message, isError]);

  const onSubmit = async (values) => {
    const body = { ...device };
    const attributes = { ...body.attributes };

    if (values.description !== '') {
      body.description = values.description;
    }
    if (values.gttSerial !== '') {
      attributes.gttSerial = values.gttSerial;
    }
    if (values.serial !== '') {
      attributes.serial = values.serial;
    }
    if (values.addressMAC !== '' && values.make === Make.SierraWireless) {
      attributes.addressMAC = values.addressMAC;
    } else if (values.make === Make.GTT) {
      attributes.addressMAC = '';
    }
    if (values.IMEI !== '' && values.make === Make.SierraWireless) {
      attributes.IMEI = values.IMEI;
    } else if (values.make === Make.GTT) {
      attributes.IMEI = '';
    }
    if (values.addressLAN !== '') {
      attributes.addressLAN = values.addressLAN;
    }
    if (values.addressWAN !== '') {
      attributes.addressWAN = values.addressWAN;
    }
    if (values.make !== '') {
      attributes.make = values.make;
    }
    if (values.make === Make.GTT && device.attributes.model === Model.MP70) {
      attributes.model = '2100';
    } else if (values.make === Make.GTT) {
      attributes.model = values.model;
    } else if (values.make === Make.SierraWireless) {
      attributes.model = 'MP-70';
    }

    body.attributes = { ...attributes };
    body.groups = { out: { ownedby: [`/${region}/${agency}`] } };
    if (vehicle) body.devices = { in: { installedat: [`${vehicle}`] } };

    delete body.direction;
    delete body.relation;

    editDevice(body);
  };

  return (
    <FormModal
      className="edit-device-modal"
      style={{ width: '700px' }}
      okText={'Save'}
      onSubmit={onSubmit}
      visible={visible}
      onCancel={onCancel}
      validationSchema={editDeviceSchema}
      validateOnChange={false}
      destroyOnClose={true}
      loading={isLoading}
      initialValues={{
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
            Device {values.deviceId} Settings
          </h1>
          <AntForm
            className="edit-device-modal-form"
            layout="vertical"
            onSubmit={handleSubmit}
            onChange={handleChange}
          >
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="Device ID"
              style={{ width: '40%' }}
            >
              <AntInput type="text" name="deviceId" value={values.deviceId} />
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="Description"
              style={{ width: '40%' }}
            >
              <AntInput
                type="text"
                name="description"
                value={values.description}
              />
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="Make"
              style={{ width: '52%' }}
            >
              <AntSelect
                allowClear
                name="make"
                onChange={(value) => setFieldValue('make', value)}
                value={values.make}
              >
                {generateMakeOptions()}
              </AntSelect>
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="Model"
              style={{ width: '25%' }}
            >
              <AntSelect
                allowClear
                name="model"
                onChange={(value) => setFieldValue('model', value)}
                value={values.model}
              >
                {values.make === Make.GTT ? (
                  <>
                    <AntSelect.Option value="2100">2100</AntSelect.Option>
                    <AntSelect.Option value="2101">2101</AntSelect.Option>
                  </>
                ) : values.make === Make.SierraWireless ? (
                  <AntSelect.Option value="MP-70">MP-70</AntSelect.Option>
                ) : values.make === Make.Cradlepoint ? (
                  <>
                    <AntSelect.Option value="IBR900">IBR900</AntSelect.Option>
                    <AntSelect.Option value="IBR1700">IBR1700</AntSelect.Option>
                    <AntSelect.Option value="R1900">R1900</AntSelect.Option>
                  </>
                ) : (
                  <></>
                )}
              </AntSelect>
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="GTT Serial"
              style={{ width: '47%' }}
            >
              <AntInput type="text" name="gttSerial" value={values.gttSerial} />
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="Serial"
              style={{ width: '47%' }}
            >
              <AntInput type="text" name="serial" value={values.serial} />
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="LAN Address"
              style={{ width: '47%' }}
            >
              <AntInput
                type="text"
                name="addressLAN"
                value={values.addressLAN}
              />
            </AntForm.Item>
            <AntForm.Item
              className="edit-device-modal-form-item"
              label="WAN Address"
              style={{ width: '47%' }}
            >
              <AntInput
                type="text"
                name="addressWAN"
                value={values.addressWAN}
              />
            </AntForm.Item>
            {(values.make === Make.SierraWireless ||
              values.make === Make.Cradlepoint) && (
              <>
                <AntForm.Item
                  className="edit-device-modal-form-item"
                  label="MAC Address"
                  style={{ width: '47%' }}
                >
                  <AntInput
                    type="text"
                    name="addressMAC"
                    value={values.addressMAC}
                  />
                </AntForm.Item>
                <AntForm.Item
                  className="edit-device-modal-form-item"
                  label="IMEI"
                  style={{ width: '47%' }}
                >
                  <AntInput type="text" name="IMEI" value={values.IMEI} />
                </AntForm.Item>
              </>
            )}
          </AntForm>
        </div>
      )}
    </FormModal>
  );
};

export default EditDeviceModal;
