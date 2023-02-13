import React, { useState, useEffect } from 'react';
import { Button, Modal } from 'antd';

const buttonMap = {
  Terminate: 'YES',
  Start: 'ACTIVE',
  Restart: 'RESTART',
  Stop: 'INACTIVE',
};

const VPSConfirmModal = ({
  showConfirmModal,
  vpsName,
  buttonName,
  setShowConfirmModal,
  response,
  editVPSS,
}) => {
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const { data, isLoading, isUninitialized } = response;
    if (!isLoading && !isUninitialized) {
      setLoading(false);
      setShowConfirmModal(false);
      setShowResponseModal(true);
    }
  }, [response, setShowConfirmModal]);

  const handleButtonClick = () => {
    setLoading(true);
    vpsName.forEach(async (name) => {
      const dockerStatus = buttonMap[buttonName];
      editVPSS({ VPSName: name, dockerStatus });
    });
  };

  const handleClose = () => {
    setShowConfirmModal(false);
  };

  const handleResponseClose = () => {
    setShowResponseModal(false);
  };

  return (
    <div className="Modals">
      <div className="ButtonModal">
        <Modal
          title={buttonName}
          visible={showConfirmModal}
          onOk={handleClose}
          onCancel={handleClose}
          footer={[
            <Button key="back" onClick={handleClose}>
              Cancel
            </Button>,
            <Button
              key="submit"
              type="primary"
              loading={loading}
              onClick={handleButtonClick}
            >
              Submit
            </Button>,
          ]}
        >
          Are you sure you want to {buttonName?.toLowerCase()} {vpsName.length}
          {' VPS?'}
          {buttonName === 'Terminate'
            ? '(Note: The VPS will also be deleted.)'
            : ''}
        </Modal>
      </div>
      <div className="ResponseModal">
        <Modal
          visible={showResponseModal}
          onOk={handleClose}
          onCancel={handleClose}
          footer={[
            <Button key="back" onClick={handleResponseClose}>
              OK
            </Button>,
          ]}
        >
          {response.isSuccess
            ? 'Device status successfully updated'
            : response.error}
        </Modal>
      </div>
    </div>
  );
};

export default VPSConfirmModal;
