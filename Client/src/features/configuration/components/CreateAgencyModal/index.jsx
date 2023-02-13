import React, { useEffect } from 'react';
import { Form as AntForm, Input as AntInput, Select as AntSelect } from 'antd';
import skeletonAgency from '../../../../templates/skeleton_agency.json';
import { agencySchema } from '../../schemas';
import FormModal from '../../../../common/components/FormModal';
import openNotification from '../../../../common/components/notification';

const { Option: AntOption } = AntSelect;

const STATE_CODES = [
  'AL',
  'AK',
  'AZ',
  'AR',
  'CA',
  'CO',
  'CT',
  'DE',
  'DC',
  'FL',
  'GA',
  'HI',
  'ID',
  'IL',
  'IN',
  'IA',
  'KS',
  'KY',
  'LA',
  'ME',
  'MD',
  'MA',
  'MI',
  'MN',
  'MS',
  'MO',
  'MT',
  'NE',
  'NV',
  'NH',
  'NJ',
  'NM',
  'NY',
  'NC',
  'ND',
  'OH',
  'OK',
  'OR',
  'PA',
  'RI',
  'SC',
  'SD',
  'TN',
  'TX',
  'UT',
  'VT',
  'VA',
  'WA',
  'WV',
  'WI',
  'WY',
];

const CreateAgencyModal = ({
  regionName,
  agencies,
  visible,
  onResponseChange,
  onCancel,
  createAgency,
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
        message: 'Error Creating Agency',
        description: error.message,
      });
    }
  }, [error?.message, isError, onResponseChange]);

  const handleSubmit = async (values, { resetForm }) => {
    const agency = { ...skeletonAgency };
    const attributes = { ...agency.attributes };
    attributes.CMSId = values.CMSId;
    attributes.city = values.city;
    attributes.state = values.state;
    attributes.timezone = values.timezone;
    attributes.agencyCode = parseInt(values.agencyCode, 10);
    attributes.priority = values.priority;
    agency.description = values.description;
    agency.name = values.name;
    agency.groupPath = `/${regionName.toLowerCase()}/${values.name.toLowerCase()}`;
    agency.parentPath = `/${regionName.toLowerCase()}`;
    agency.attributes = attributes;
    createAgency(agency);
  };

  return (
    <FormModal
      title="Create New Agency"
      onSubmit={handleSubmit}
      onCancel={onCancel}
      visible={visible}
      destroyOnClose={true}
      loading={isLoading}
      enableReinitialize
      validationSchema={agencySchema}
      validateOnChange={false}
      initialValues={{
        name: '',
        description: '',
        city: '',
        state: '',
        timezone: '',
        agencyCode: '',
        priority: '',
        CMSId: '',
      }}
      agencies={agencies}
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
            <AntForm.Item label="Name" help={errors.name} required>
              <AntInput type="text" name="name" disabled={isSubmitting} />
            </AntForm.Item>
            <AntForm.Item label="Description" help={errors.description}>
              <AntInput
                type="text"
                name="description"
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </AntForm.Item>
            <AntForm.Item label="Priority" help={errors.priority} required>
              <AntSelect
                allowClear
                name="priority"
                onChange={(value) => setFieldValue('priority', value)}
                disabled={isSubmitting}
              >
                <AntOption value="High">High</AntOption>
                <AntOption value="Low">Low</AntOption>
              </AntSelect>
            </AntForm.Item>

            <AntForm.Item label="Agency Code" help={errors.agencyCode} required>
              <AntInput
                type="text"
                name="agencyCode"
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </AntForm.Item>
            <AntForm.Item label="City" help={errors.city} required>
              <AntInput
                type="text"
                name="city"
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </AntForm.Item>

            <AntForm.Item label="State" help={errors.state} required>
              <AntSelect
                allowClear
                name="state"
                onChange={(value) => setFieldValue('state', value)}
                disabled={isSubmitting}
              >
                {STATE_CODES.map((code) => (
                  <AntOption value={code} key={code}>
                    {code}
                  </AntOption>
                ))}
              </AntSelect>
            </AntForm.Item>

            <AntForm.Item label="Time Zone" help={errors.timezone} required>
              <AntSelect
                allowClear
                name="timezone"
                onChange={(value) => setFieldValue('timezone', value)}
                disabled={isSubmitting}
              >
                <AntOption value="Central">Central</AntOption>
                <AntOption value="Mountain">Mountain</AntOption>
                <AntOption value="Eastern">Eastern</AntOption>
                <AntOption value="Pacific">Pacific</AntOption>
                <AntOption value="Arizona">Arizona</AntOption>
              </AntSelect>
            </AntForm.Item>

            <AntForm.Item label="CMS ID" help={errors.CMSId}>
              <AntSelect
                allowClear
                onChange={(value) => setFieldValue('CMSId', value)}
                disabled={isSubmitting}
                defaultValue=""
              >
                <AntOption value="">
                  <i>Create new CMS ID</i>
                </AntOption>
                {agencies &&
                  agencies.length &&
                  agencies.map((agency, index) => (
                    <AntOption key={index + 1} value={agency.CMSId}>
                      {agency.CMSId} ({agency.Name})
                    </AntOption>
                  ))}
              </AntSelect>
            </AntForm.Item>
          </AntForm>
        </div>
      )}
    </FormModal>
  );
};

export default CreateAgencyModal;
