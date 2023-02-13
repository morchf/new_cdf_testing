import React, { useEffect } from 'react';
import { Form as AntForm, Input as AntInput } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import skeletonRegion from '../../../../templates/skeleton_region.json';
import { regionSchema } from '../../schemas';
import openNotification from '../../../../common/components/notification';

const CreateRegionModal = ({
  visible,
  onResponseChange,
  onCancel,
  createRegion,
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
        message: 'Error Creating Region',
        description: error.message,
      });
    }
  }, [error?.message, isError, onResponseChange]);

  const onSubmit = async (values, { resetForm }) => {
    const region = { ...skeletonRegion };
    region.description = values.description;
    region.name = values.name;
    region.groupPath = `/${values.name.toLowerCase()}`;
    createRegion(region);
  };

  return (
    <FormModal
      title="Create New Region"
      onSubmit={onSubmit}
      onCancel={onCancel}
      visible={visible}
      destroyOnClose={true}
      loading={isLoading}
      validationSchema={regionSchema}
      validateOnChange={false}
      initialValues={{
        name: '',
        description: '',
      }}
    >
      {({ handleSubmit, handleChange, isSubmitting, errors }) => (
        <div>
          <AntForm
            labelCol={{ span: 6 }}
            wrapperCol={{ span: 12 }}
            onSubmit={handleSubmit}
            onChange={handleChange}
          >
            <AntForm.Item label="Name" help={errors.name} required>
              <AntInput
                type="text"
                name="name"
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </AntForm.Item>

            <AntForm.Item label="Description" help={errors.description}>
              <AntInput
                type="text"
                name="description"
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </AntForm.Item>
          </AntForm>
        </div>
      )}
    </FormModal>
  );
};

export default CreateRegionModal;
