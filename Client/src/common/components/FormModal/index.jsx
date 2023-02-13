import { Modal as AntModal, Typography as AnyTypography } from 'antd';
import { Formik } from 'formik';
import { useRef, useState } from 'react';

const { Title: AntTitle } = AnyTypography;

const FormModal = ({
  title,
  visible,
  onSubmit,
  onCancel,
  destroyOnClose,
  children,
  cancelText,
  loading,
  ...props
}) => {
  const [confirmLoading, setConfirmLoading] = useState(false);
  const formRef = useRef();

  const handleSubmit = async (values, { resetForm }) => {
    setConfirmLoading(true);
    await onSubmit(values, { resetForm });
    setConfirmLoading(false);
  };

  const handleOk = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };

  return (
    <AntModal
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading || loading}
      visible={visible}
      destroyOnClose={destroyOnClose}
      okText="Submit"
      cancelText={cancelText}
      {...props}
    >
      {title && (
        <AntTitle level={5} style={{ marginBottom: '1.5rem' }}>
          {title}
        </AntTitle>
      )}
      <Formik innerRef={formRef} onSubmit={handleSubmit} {...props}>
        {children}
      </Formik>
    </AntModal>
  );
};

export default FormModal;
