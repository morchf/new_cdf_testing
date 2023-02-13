import React, { useState, useEffect, useRef } from 'react';
import { Form, Input, Button, Modal } from 'antd';
import useVPSList from '../../hooks/useVPSList';

const Provision = ({ customerName }) => {
  const [showModal, setShowModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [status, setStatus] = useState(null);

  const { edit, editVPSSResponse } = useVPSList({
    customerName,
  });

  const formRef = useRef(null);

  useEffect(() => {
    const { data, isLoading, isUninitialized } = editVPSSResponse;
    if (!isLoading && !isUninitialized) {
      if (data.status) {
        setStatus(data.status);
        setMessage(data.data);
      } else {
        setStatus(data.response.status);
        setMessage(data.response.data);
      }
      setShowModal(true);
      setUploading(false);
      formRef.current.resetFields();
    }
  }, [editVPSSResponse]);

  // Create new vps and POST to api

  const handleClose = () => {
    setShowModal(false);
  };

  const onFinish = async (values) => {
    setUploading(true);
    edit({
      customer: customerName.toUpperCase(),
      deviceprefix: values.devicePrefix,
      number: parseInt(values.count, 10),
    });
  };

  const onFinishFailed = (errorInfo) => {
    console.log('Failed:', errorInfo);
  };

  return (
    <div style={{ display: 'flex', marginTop: '5%' }}>
      <div className="Provison" style={{ width: 300 }}>
        <h5 className="text-left">Provison</h5>
        <Form
          name="basic"
          labelCol={{
            span: 8,
          }}
          wrapperCol={{
            span: 16,
          }}
          initialValues={{
            remember: true,
            deviceprefix: '',
            count: '',
          }}
          requiredMark="optional"
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
          autoComplete="off"
          ref={formRef}
        >
          <Form.Item
            label="Device Prefix"
            name="devicePrefix"
            rules={[
              {
                required: true,
                message: 'Device prefix is required',
              },
              {
                pattern: /^[a-zA-Z0-9]+$/,
                message: 'Device Prefix can only include letters and numbers.',
              },
            ]}
          >
            <Input placeholder="V764" />
          </Form.Item>

          <Form.Item
            label="Count"
            name="count"
            rules={[
              {
                required: true,
                message: 'Count is required',
              },
              {
                pattern: '^([1-9]|[1-9][0-9]|[1][0-9][0-9]|20[0-0])$',
                message: 'Count must be an integer from 1 to 200',
              },
            ]}
          >
            <Input />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={uploading}>
            Submit
          </Button>
        </Form>

        <Modal
          title={status !== 200 ? 'Error' : 'Success'}
          visible={showModal}
          onOk={handleClose}
          onCancel={handleClose}
        >
          {message}
        </Modal>
      </div>
    </div>
  );
};

export default Provision;
