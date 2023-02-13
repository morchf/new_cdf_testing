import React, { useEffect } from 'react';
import { Form as AntForm, Input as AntInput } from 'antd';
import FormModal from '../../../../common/components/FormModal';
import { intersectionSchema } from '../../schemas';
import openNotification from '../../../../common/components/notification';
import useCreateIntersection from '../../hooks/useCreateIntersection';
import useRelativeNavigate from '../../../../common/hooks/useRelativeNavigate';

const AddIntersectionModal = ({ visible, onCancel }) => {
  const { create, newIntersection, error, isLoading, isSuccess } =
    useCreateIntersection();
  const navigate = useRelativeNavigate();

  useEffect(() => {
    if (isSuccess) {
      openNotification({
        message: newIntersection,
        type: 'success',
      });
    }
  }, [isSuccess, isLoading, newIntersection]);

  useEffect(() => {
    if (error) {
      openNotification({
        message: 'Error Creating Intersection',
        description: error,
      });
    }
  }, [error, isLoading, newIntersection]);

  useEffect(() => {
    if (newIntersection) {
      navigate(newIntersection.serialNumber);
    }
  }, [navigate, newIntersection]);

  return (
    <div className="Create">
      <FormModal
        title="Please enter name and coordinates for new intersection"
        onSubmit={create}
        visible={visible}
        onCancel={onCancel}
        destroyOnClose={true}
        validationSchema={intersectionSchema}
        validateOnChange={false}
        loading={isLoading}
        initialValues={{
          intersectionName: '',
          longitude: '',
          latitude: '',
        }}
      >
        {({
          handleSubmit: onSubmit,
          handleChange,
          values,
          isSubmitting,
          errors,
          setFieldValue,
        }) => (
          <div>
            <AntForm
              labelCol={{ span: 6 }}
              wrapperCol={{ span: 12 }}
              onSubmit={onSubmit}
              onChange={handleChange}
            >
              <AntForm.Item
                label="Name"
                help={errors.intersectionName}
                required
              >
                <AntInput
                  type="text"
                  name="intersectionName"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="Latitude" help={errors.latitude} required>
                <AntInput
                  type="text"
                  name="latitude"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
              <AntForm.Item label="Longitude" help={errors.longitude} required>
                <AntInput
                  type="text"
                  name="longitude"
                  onChange={handleChange}
                  disabled={isSubmitting}
                />
              </AntForm.Item>
            </AntForm>
          </div>
        )}
      </FormModal>
    </div>
  );
};

export default AddIntersectionModal;
