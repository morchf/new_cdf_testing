import React, { useEffect, useRef, useState } from 'react';
import { connect } from 'react-redux';
import { Upload, Button, Modal, Row, Col } from 'antd';
import { DownloadOutlined, UploadOutlined } from '@ant-design/icons';
import { useUploadStaticIntersectionsMutation } from '../../api';
import './style.css';

const UploadFile = ({
  children,
  modalContent,
  isLoading,
  error,
  onSubmit,
  template,
}) => {
  const [fileList, setFileList] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const fileRef = useRef();

  const handleUpload = async () => {
    const formData = new FormData();

    formData.append('file', fileList[0]);
    formData.append('type', fileList[0]?.name.split('.').pop());

    onSubmit(formData);
  };

  const handleDownload = () => {
    if (fileRef.current) {
      fileRef.current.click();
    }
  };

  useEffect(() => {
    if (!modalContent) return;

    setShowModal(true);
  }, [modalContent, setShowModal]);

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
    <div style={{ display: 'flex', padding: '1rem 0rem' }}>
      <div>
        <Row gutter={[16, 0]}>
          <Col>
            <Upload {...props}>
              <Button
                disabled={fileList.length === 1}
                icon={<UploadOutlined />}
              >
                Select File
              </Button>
            </Upload>
          </Col>
          <Col>
            <Button
              type="primary"
              onClick={handleUpload}
              disabled={fileList.length === 0}
              loading={isLoading}
            >
              {isLoading ? 'Uploading' : 'Upload'}
            </Button>
          </Col>
          {template && (
            <Col>
              <a
                ref={fileRef}
                style={{ display: 'none' }}
                href={template}
                download={template.split('/').pop()}
              />
              <Button
                type="primary"
                onClick={handleDownload}
                icon={<DownloadOutlined />}
              >
                Template
              </Button>
            </Col>
          )}
        </Row>

        {children}

        <Modal
          title={error && 'Error'}
          visible={showModal}
          onOk={handleClose}
          onCancel={handleClose}
          footer={[
            <Button key="submit" type="primary" onClick={handleClose}>
              OK
            </Button>,
          ]}
        >
          {modalContent}
        </Modal>
      </div>
    </div>
  );
};

const UploadStaticIntersections = ({ region, agency }) => {
  const [upload, { isLoading, error, data, isError, isSuccess }] =
    useUploadStaticIntersectionsMutation();

  const handleSubmit = (formData) => {
    upload({ data: formData, regionName: region, agencyName: agency });
  };

  return (
    <div className="upload-static-intersections">
      <p className="text-left upload-static-intersections__title">
        Upload Static intersections
      </p>
      <UploadFile
        onSubmit={handleSubmit}
        modalContent={
          isSuccess ? 'Success' : isError && 'Error uploading intersections'
        }
        isLoading={isLoading}
        error={error}
        template="/resources/templates/Upload Static Intersections.csv"
      />
    </div>
  );
};

const mapStateToProps = ({ user }) => {
  const { region, agency } = user;
  return { region, agency };
};

export default connect(mapStateToProps)(UploadStaticIntersections);
