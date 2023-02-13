import React, { useState, useEffect } from 'react';
import { Form as AntForm, Input as AntInput, Row } from 'antd';
import { editRegionSchema } from '../../schemas';
import FormModal from '../../../../common/components/FormModal';
import openNotification from '../../../../common/components/notification';
import Table from '../../../../common/components/Table';
import Button from '../../../../common/components/Button';

const EditRegion = ({ region, editRegion, response }) => {
  const [showEditTable, setShowEditTable] = useState(false);
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
        message: 'Error Editing Region',
        description: error.message,
      });
  }, [error?.message, isError]);

  const onSubmit = async (values) => {
    const body = { ...region };
    if (body.description !== values.description) {
      body.description = values.description;
    }
    editRegion(body);
    setShowEditTable(true);
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
  ];

  function RegionTable({ region: r }) {
    if (!r || r.length === 0) {
      return <p>No r data</p>;
    }
    const tableItems = [
      {
        key: r.name,
        ...r,
      },
    ];
    return (
      <div className="SearchTable">
        <Table
          columns={columns}
          dataSource={tableItems}
          pagination={false}
          bordered={false}
        />
      </div>
    );
  }

  return (
    <div className="Edit">
      {showEditTable ? (
        <FormModal
          title="Edit Region"
          onSubmit={onSubmit}
          visible={showEditTable}
          onCancel={() => setShowEditTable(false)}
          loading={isLoading}
          validationSchema={editRegionSchema}
          validateOnChange={false}
          initialValues={{
            name: region.name,
            description: region.description,
          }}
        >
          {({ handleSubmit, handleChange, values, errors, isSubmitting }) => (
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
              </AntForm>
            </div>
          )}
        </FormModal>
      ) : (
        <div>
          <RegionTable region={region} />
          <Button
            type="secondary"
            size="md"
            location="right"
            onClick={() => setShowEditTable(true)}
          >
            Edit Properties
          </Button>
        </div>
      )}
    </div>
  );
};

export default EditRegion;
