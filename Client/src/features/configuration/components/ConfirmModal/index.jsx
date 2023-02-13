import React, { useEffect, useState } from 'react';
import { Modal as AntModal, Button } from 'antd';
import openNotification from '../../../../common/components/notification';

const ConfirmModal = ({
  visible,
  onResponseChange,
  onSelectedChange,
  body,
  selected,
  response,
  delete: deleteEntity,
}) => {
  const [showButtonModal, setShowButtonModal] = useState(false);
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const { data, isLoading, isSuccess, isError, error } = response;
  const errorMessage = error?.message;

  useEffect(() => {
    if (visible && selected.length !== 0 && !deleting) setShowButtonModal(true);
    if (visible && selected.length === 0) {
      onResponseChange();
      openNotification({
        message: 'Error',
        description: (
          <p>
            You should select at least one of the {Object.keys(body)[0]} at a
            time.
          </p>
        ),
      });
    }
  }, [visible, selected, deleting, onResponseChange, body]);

  useEffect(() => {
    if (isSuccess) {
      setShowButtonModal(false);
      setShowResponseModal(true);
    }
  }, [isSuccess]);

  useEffect(() => {
    if (isError)
      openNotification({
        message: 'Deletion Error',
        description: errorMessage,
      });
  }, [isError, errorMessage]);

  const handleButtonClick = async (event) => {
    setDeleting(true);
    const entityType = Object.keys(body)[0];
    if (body[entityType].length === 0) setShowButtonModal(false);
    else {
      event.preventDefault();
      deleteEntity(body);
    }
  };

  const handleClose = () => {
    onResponseChange();
    setShowButtonModal(false);
  };

  const handleResponseClose = () => {
    setDeleting(false);
    setShowResponseModal(false);
    onResponseChange();
    onSelectedChange();
  };

  return (
    <div className="Modals">
      {visible && (
        <div>
          <div className="ButtonModal">
            <AntModal
              confirmLoading={isLoading}
              onOk={handleButtonClick}
              onCancel={handleClose}
              visible={showButtonModal}
              okText="Submit"
              cancelText="Cancel"
              title="Delete"
            >
              <p>Are you sure you want to delete {selected.join(', ')}?</p>
            </AntModal>
          </div>
          <div className="ResponseModal">
            <AntModal
              onCancel={handleResponseClose}
              visible={showResponseModal}
              style={{
                marginTop: '12%',
              }}
              footer={[
                <Button key="ok" type="primary" onClick={handleResponseClose}>
                  Ok
                </Button>,
              ]}
            >
              <p>
                {data} {selected.join(', ')}
              </p>
            </AntModal>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfirmModal;
