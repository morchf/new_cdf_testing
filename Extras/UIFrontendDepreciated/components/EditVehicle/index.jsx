import React, { useState, useEffect } from 'react';
import { Form as AntForm, Input as AntInput, Select as AntSelect } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import { editVehicleSchema } from '../../schemas';
import openNotification from '../../../../common/components/notification';
import Button from '../../../../common/components/Button';
import Table from '../../../../common/components/Table';
import './style.css';

const EditVehicle = ({ vehicle, editVehicle, response }) => {
  const [showEditTable, setShowEditTable] = useState(false);
  const [windowSize, setWindowSize] = useState(undefined);
  const { data, isLoading, isSuccess, isError, error } = response;

  useEffect(() => {
    if (isSuccess) {
      openNotification({
        message: data,
        type: 'success',
      });
      setShowEditTable(false);
    }
  }, [data, isSuccess]);

  useEffect(() => {
    if (isError)
      openNotification({
        message: 'Error Editing Vehicle',
        description: error.message,
      });
  }, [error?.message, isError]);

  useEffect(() => {
    const handleResize = async (e) => {
      setWindowSize(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
  }, []);

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
    editVehicle(body);
  };

  const columns = [
    {
      key: 'key',
      dataIndex: 'key',
      title: 'Name',
    },
    {
      key: 'description',
      dataIndex: 'description',
      title: 'Description',
    },
    {
      key: 'priority',
      dataIndex: 'priority',
      title: 'Priority',
    },
    {
      key: 'type',
      dataIndex: 'type',
      title: 'Type',
    },
    {
      key: 'VID',
      dataIndex: 'VID',
      title: 'VID',
    },
    {
      key: 'class',
      dataIndex: 'class',
      title: 'Class',
    },
    {
      key: 'deviceId',
      dataIndex: 'deviceId',
      title: 'Device ID',
    },
  ];

  function VehicleTable({ vehicle: v }) {
    const tableItems =
      !v || v.length === 0
        ? null
        : [
            {
              key: v.attributes.name,
              description: v.description,
              deviceId: v.deviceId,
              ...v.attributes,
            },
          ];
    return (
      <div className="VehicleTable">
        <Table
          columns={columns}
          dataSource={tableItems}
          pagination={false}
          bordered={false}
          scroll={windowSize < 1600 ? { x: 1200 } : {}}
        />
      </div>
    );
  }

  return (
    <div className="Edit">
      {showEditTable ? (
        <FormModal
          title="Edit Vehicle"
          onSubmit={onSubmit}
          visible={showEditTable}
          onCancel={() => setShowEditTable(false)}
          loading={isLoading}
          validationSchema={editVehicleSchema}
          validateOnChange={false}
          initialValues={{
            name: vehicle.attributes.name,
            description: vehicle.description,
            type: vehicle.attributes.type,
            VID: vehicle.attributes.VID,
            class: vehicle.attributes.class,
            priority: vehicle.attributes.priority,
            deviceId: vehicle.deviceId,
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
              <AntForm
                labelCol={{ span: 6 }}
                wrapperCol={{ span: 12 }}
                onSubmit={handleSubmit}
                onChange={handleChange}
              >
                <AntForm.Item label="Name" help={errors.name}>
                  <AntInput
                    type="text"
                    name="name"
                    onChange={handleChange}
                    disabled={true}
                    value={values.name}
                  />
                </AntForm.Item>
                <AntForm.Item label="Description" help={errors.description}>
                  <AntInput
                    type="text"
                    name="description"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.description}
                  />
                </AntForm.Item>
                <AntForm.Item label="Priority" help={errors.priority}>
                  <AntSelect
                    name="priority"
                    disabled={isSubmitting}
                    onChange={(value) => setFieldValue('priority', value)}
                    defaultValue={values.priority}
                  >
                    <AntSelect.Option value="High">High</AntSelect.Option>
                    <AntSelect.Option value="Low">Low</AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>
                <AntForm.Item label="Type" help={errors.type}>
                  <AntInput
                    type="text"
                    name="type"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.type}
                  />
                </AntForm.Item>
                <AntForm.Item label="VID" help={errors.VID}>
                  <AntInput
                    type="text"
                    name="VID"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.VID}
                  />
                </AntForm.Item>
                <AntForm.Item label="Class" help={errors.class}>
                  <AntInput
                    type="text"
                    name="class"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.class}
                  />
                </AntForm.Item>
                <AntForm.Item label="Device ID" help={errors.deviceId}>
                  <AntInput
                    type="text"
                    name="deviceId"
                    onChange={handleChange}
                    disabled={true}
                    value={values.deviceId}
                  />
                </AntForm.Item>
              </AntForm>
            </div>
          )}
        </FormModal>
      ) : (
        <div>
          <h5>Vehicle Properties</h5>
          <VehicleTable vehicle={vehicle} />
          <Button
            type="secondary"
            size="lg"
            location="right"
            onClick={() => setShowEditTable(true)}
          >
            Edit Properties
          </Button>{' '}
        </div>
      )}
    </div>
  );
};

export default EditVehicle;
