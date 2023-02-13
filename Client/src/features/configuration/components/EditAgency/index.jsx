import React, { useState, useEffect } from 'react';
import { Form as AntForm, Input as AntInput, Select as AntSelect } from 'antd';
import { agencySchema } from '../../schemas';
import FormModal from '../../../../common/components/FormModal';
import openNotification from '../../../../common/components/notification';
import Table from '../../../../common/components/Table';
import Button from '../../../../common/components/Button';
import './style.css';

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

const EditAgency = ({ agencies, agency, editAgency, response }) => {
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
        message: 'Error Editing Agency',
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
    const body = { ...agency };
    const attributes = { ...body.attributes };
    Object.keys(attributes).forEach((key, value) => {
      if (Object.prototype.hasOwnProperty.call(values, key)) {
        if (key === 'agencyCode') attributes[key] = parseInt(values[key], 10);
        else attributes[key] = values[key];
      }
    });
    body.attributes = { ...attributes };
    if (values.name !== '') {
      body.name = values.name;
    }
    if (values.description !== '') {
      body.description = values.description;
    }
    editAgency(body);
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
      key: 'agencyCode',
      dataIndex: 'agencyCode',
      title: 'Agency Code',
    },
    {
      key: 'city',
      dataIndex: 'city',
      title: 'City',
    },
    {
      key: 'state',
      dataIndex: 'state',
      title: 'State',
    },
    {
      key: 'timezone',
      dataIndex: 'timezone',
      title: 'Timezone',
    },
    {
      key: 'CMSId',
      dataIndex: 'CMSId',
      title: 'CMS ID',
    },
    {
      title: '',
      dataIndex: 'operation',
      render: () =>
        <Button
        type="secondary"
        size="lg"
        location="right"
        onClick={() => setShowEditTable(true)}
      >
        Edit Properties
      </Button>
    },
  ];

  function AgencyTable({ agency: a }) {
    const tableItems =
      !a || a.length === 0
        ? null
        : [
            {
              key: a.name,
              description: a.description,
              ...a.attributes,
            },
          ];
    return (
      <div className="AgencyTable">
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
          title="Edit Agency"
          onSubmit={onSubmit}
          visible={showEditTable}
          onCancel={() => setShowEditTable(false)}
          loading={isLoading}
          validationSchema={agencySchema}
          validateOnChange={false}
          initialValues={{
            name: agency.name,
            description: agency.description,
            city: agency.attributes.city,
            state: agency.attributes.state.toUpperCase(),
            timezone: agency.attributes.timezone,
            agencyCode: agency.attributes.agencyCode,
            priority: agency.attributes.priority,
            CMSId: agency.attributes.CMSId,
          }}
          agencies={agencies}
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
                <AntForm.Item label="Name" help={errors.name} required>
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
                <AntForm.Item label="Priority" help={errors.priority} required>
                  <AntSelect
                    allowClear
                    name="priority"
                    onChange={(value) => setFieldValue('priority', value)}
                    disabled={isSubmitting}
                    value={values.priority}
                  >
                    <AntSelect.Option value="High">High</AntSelect.Option>
                    <AntSelect.Option value="Low">Low</AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>

                <AntForm.Item
                  label="Agency Code"
                  help={errors.agencyCode}
                  required
                >
                  <AntInput
                    type="text"
                    name="agencyCode"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.agencyCode}
                  />
                </AntForm.Item>
                <AntForm.Item label="City" help={errors.city} required>
                  <AntInput
                    type="text"
                    name="city"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.city}
                  />
                </AntForm.Item>

                <AntForm.Item label="State" help={errors.state} required>
                  <AntSelect
                    allowClear
                    name="state"
                    onChange={(value) => setFieldValue('state', value)}
                    disabled={isSubmitting}
                    value={values.state}
                  >
                    {STATE_CODES.map((code) => (
                      <AntSelect.Option value={code} key={code}>
                        {code}
                      </AntSelect.Option>
                    ))}
                  </AntSelect>
                </AntForm.Item>

                <AntForm.Item label="Time Zone" help={errors.timezone} required>
                  <AntSelect
                    allowClear
                    name="timezone"
                    onChange={(value) => setFieldValue('timezone', value)}
                    disabled={isSubmitting}
                    value={values.timezone}
                  >
                    <AntSelect.Option value="Central">Central</AntSelect.Option>
                    <AntSelect.Option value="Mountain">
                      Mountain
                    </AntSelect.Option>
                    <AntSelect.Option value="Eastern">Eastern</AntSelect.Option>
                    <AntSelect.Option value="Pacific">Pacific</AntSelect.Option>
                    <AntSelect.Option value="Arizona">Arizona</AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>

                <AntForm.Item label="CMS ID" help={errors.CMSId}>
                  <AntSelect
                    allowClear
                    onChange={(value) => setFieldValue('CMSId', value)}
                    disabled={isSubmitting}
                    value={values.CMSId}
                  >
                    {agencies &&
                      agencies.length &&
                      agencies.map(({ CMSId, Name }, index) => (
                        <AntSelect.Option key={index + 1} value={CMSId}>
                          {CMSId} ({Name})
                        </AntSelect.Option>
                      ))}
                  </AntSelect>
                </AntForm.Item>
              </AntForm>
            </div>
          )}
        </FormModal>
      ) : (
        <div style={{marginTop:'1em'}}>
          <h5>Agency Properties</h5>

          <AgencyTable agency={agency} />
        </div>
      )}
    </div>
  );
};

export default EditAgency;
