import React, { useState, useEffect } from 'react';
import { Upload, Button, Modal } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import useConfigCMS from '../../hooks/useConfigCMS';

const ConfigCMS = () => {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const {
    configCMSResponse,
    isLoading,
    isUninitialized,
    status,
    message,
    configCMS,
  } = useConfigCMS();

  useEffect(() => {
    if (!isLoading && !isUninitialized) {
      setShowModal(true);
      setFileList([]);
      setUploading(false);
    }
  }, [configCMSResponse, isLoading, isUninitialized]);

  // import csv file and POST to api

  const handleUpload = async () => {
    setUploading(true);
    configCMS(fileList[0], { 'Content-Type': 'application/csv' });
  };

  const handleClose = () => {
    setShowModal(false);
  };

  const props = {
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file) => {
      setFileList([...fileList, file]);
      return false;
    },
    fileList,
    maxCount: 1,
    multiple: false,
  };

  return (
    <div style={{ display: 'flex', marginTop: '5%' }}>
      <div className="ImportCSV">
        <h5 className="text-left">Import Configure File</h5>
        <Upload {...props}>
          {/* disabled the import feature until backend is fixed */}
          <Button icon={<UploadOutlined />} disabled>
            Select File
          </Button>
        </Upload>
        <Button
          type="primary"
          onClick={handleUpload}
          disabled={fileList.length === 0}
          loading={uploading}
          style={{ marginTop: 16 }}
        >
          {uploading ? 'Uploading' : 'Start Upload'}
        </Button>
        <Modal
          title={!isUninitialized && status !== 'success' ? 'Error' : 'Success'}
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

export default ConfigCMS;
