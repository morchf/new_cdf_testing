import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Form as AntForm, Input as AntInput, Select as AntSelect } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import skeletonVehicle from '../../../../templates/skeleton_vehicle.json';
import { vehicleSchema } from '../../schemas';
import openNotification from '../../../../common/components/notification';
import './style.css';

const CreateVehicle = ({
  visible,
  agencyGroupPath,
  onResponseChange,
  onCancel,
  createVehicle,
  response,
}) => {
  const { data, isLoading, isSuccess, isError, error } = response;

  const { agency } = useSelector(({ configuration }) => configuration);

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
        message: 'Error Creating Vehicle',
        description: error.message,
      });
    }
  }, [error?.message, isError, onResponseChange]);

  const onSubmit = async (values, { resetForm }) => {
    const attributes = { ...values };

    const skeleton = { ...skeletonVehicle };
    const skeletonAttributes = { ...skeleton.attributes };
    const groups = { ...skeleton.groups };

    skeletonAttributes.name = attributes.name;
    skeleton.description = attributes.description;
    skeletonAttributes.type = attributes.type;
    skeletonAttributes.class = parseInt(attributes.class, 10);
    skeletonAttributes.VID = parseInt(attributes.VID, 10);
    skeletonAttributes.priority = attributes.priority;
    groups.ownedby = JSON.parse(`["${agencyGroupPath}"]`);

    skeleton.attributes = skeletonAttributes;
    skeleton.groups = groups;
    createVehicle(skeleton);
  };

  return (
    <div className="Create">
      <FormModal
        className="create-vehicle-modal"
        onSubmit={onSubmit}
        visible={visible}
        onCancel={onCancel}
        destroyOnClose={true}
        loading={isLoading}
        validationSchema={vehicleSchema}
        validateOnChange={false}
        initialValues={{
          name: '',
          description: '',
          type: '',
          VID: 1,
          class: 10,
          priority: '',
        }}
      >
        {({
          handleSubmit,
          handleChange,
          values,
          isSubmitting,
          errors,
          setFieldValue,
        }) => (
          <div>
            <h1 style={{ textAlign: 'center', margin: 0, marginBottom: '3%' }}>
              Create a New Vehicle
            </h1>
            <AntForm
              className="create-vehicle-modal-form"
              labelCol={{ span: 6 }}
              wrapperCol={{ span: 12 }}
              onSubmit={handleSubmit}
              onChange={handleChange}
              initialValues={{
                name: '',
                description: '',
                type: '',
                VID: 1,
                class: 10,
                priority: '',
              }}
            >
              <AntForm.Item label="Name" help={errors.name} required>
                <AntInput
                  type="text"
                  name="name"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="Type" help={errors.type}>
                <AntInput
                  type="text"
                  name="type"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="Priority" help={errors.priority} required>
                <AntSelect
                  name="priority"
                  disabled={isSubmitting}
                  onChange={(value) => setFieldValue('priority', value)}
                >
                  {agency.attributes.priority === 'High' ? (
                    <>
                      <AntSelect.Option value="High">High</AntSelect.Option>
                      <AntSelect.Option value="Low">Low</AntSelect.Option>
                    </>
                  ) : (
                    <AntSelect.Option value="Low">Low</AntSelect.Option>
                  )}
                </AntSelect>
              </AntForm.Item>
              <AntForm.Item label="Description" help={errors.description}>
                <AntInput
                  type="text"
                  name="description"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="VID" help={errors.VID}>
                <AntInput
                  type="text"
                  name="VID"
                  onChange={handleChange}
                  disabled={isSubmitting}
                  defaultValue="1"
                />
              </AntForm.Item>
              <AntForm.Item label="Class" help={errors.class}>
                <AntInput
                  type="text"
                  name="class"
                  onChange={handleChange}
                  disabled={isSubmitting}
                  defaultValue="10"
                />
              </AntForm.Item>
            </AntForm>
          </div>
        )}
      </FormModal>
    </div>
  );
};

export default CreateVehicle;
