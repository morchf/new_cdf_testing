import React, { useState, useEffect, useMemo } from 'react';
import moment from 'moment';
import { Upload, Button, Modal, Input, Tooltip, Row, Col } from 'antd';
import {
  UploadOutlined,
  UserOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { connect } from 'react-redux';
import useImportCSV from '../../hooks/useImportCSV';

const NO_OWNER_TAG = 'NO-OWNER';

const ImportCSV = ({ title, uploadURL }) => {
  const [email, setEmail] = useState(null);
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [message, setMessage] = useState(null);
  const [status, setStatus] = useState(null);
  const [jobId, setJobId] = useState();

  const { getCSVResponse: uploadResponse, getCSV: upload } = useImportCSV();
  const { getCSVResponse: statusResponse, getCSV: updateStatus } =
    useImportCSV();

  useEffect(() => {
    const { isLoading, isSuccess, isUninitialized } = uploadResponse;
    if (!isLoading && !isUninitialized) {
      if (isSuccess) {
        setJobId(uploadResponse.data.QueueUrl);
        setStatus(uploadResponse.status);
        setMessage('Upload successful');
      } else if (uploadResponse.isError) {
        setStatus(400);
        setMessage('Unknown error');
      } else {
        setStatus(uploadResponse.status);
        setMessage(uploadResponse.data);
      }

      setShowModal(true);
      setFileList([]);
      setUploading(false);
    }
  }, [uploadResponse]);

  useEffect(() => {
    const { isLoading, isSuccess, isUninitialized } = statusResponse;
    if (!isLoading && !isUninitialized) {
      if (isSuccess) {
        const { data } = statusResponse;
        const startTime = moment(data.StartTimestamp * 1000).format(
          'M/D/YYYY h:mmA'
        );
        const retrieveTime = moment().format('M/D/YYYY h:mm:ssA');

        const messageText = `
        ${data.Done ? 'Done' : 'In Progress'} | Started: ${startTime}
        Errors: ${data.NumberOfErrors}
        Messages being processed: ${data.NumberOfMessagesBeingProcessed}
        Messages remaining: ${data.NumberOfMessagesRemaining}
        
        Last updated: ${retrieveTime}`;

        setStatus(statusResponse.status);
        setMessage(messageText);
        if (data.Done) {
          setJobId(null);
        }
      } else {
        setStatus(statusResponse.status);
        setMessage('Error loading job status. May have finished');
        setJobId(null);
      }

      setShowModal(true);
    }
  }, [statusResponse]);

  // import csv file and POST to api
  const handleUpload = async () => {
    const formData = new FormData();

    let owner = NO_OWNER_TAG;
    try {
      owner = email.split('@')[0].split('.').join('-');
      // eslint-disable-next-line no-empty
    } catch {}

    formData.append('file', fileList[0]);
    formData.append('type', fileList[0]?.name.split('.').pop());
    setUploading(true);

    upload(
      formData,
      { type: 'create', email, owner },
      { 'Content-Type': 'multipart/form-data', Accept: 'multipart/form-data' },
      uploadURL
    );
  };

  const handleStatus = async (queueUrl) => {
    updateStatus({}, { type: 'status', queue_url: queueUrl }, {}, uploadURL);
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

  const jobStatus = useMemo(
    () => `Check Status (${jobId ? 1 : 0} Job${jobId ? '' : 's'})`,
    [jobId]
  );

  return (
    <div style={{ display: 'flex', padding: '1rem 0rem' }}>
      <div className="ImportCSV">
        <p className="text-left">{title}</p>
        <Input
          placeholder="Enter your email address"
          type="email"
          prefix={<UserOutlined className="site-form-item-icon" />}
          suffix={
            <Tooltip title="An email will be sent to this email address if any error. Must confirm email on first batch creation">
              <InfoCircleOutlined style={{ color: 'rgba(0,0,0,.45)' }} />
            </Tooltip>
          }
          onChange={(e) => setEmail(e.target.value)}
        />
        <Row gutter={[16, 0]}>
          <Col>
            <Upload {...props}>
              <Button
                disabled={fileList.length === 1}
                style={{ marginTop: 16 }}
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
              loading={uploading}
              style={{ marginTop: 16 }}
            >
              {uploading ? 'Uploading' : 'Upload'}
            </Button>
          </Col>
          <Col>
            <Tooltip
              placement="right"
              title="Check status button will be disabled once you refresh or leave the page"
            >
              <Button
                type="primary"
                onClick={() => handleStatus(jobId)}
                disabled={!jobId}
                style={{ marginTop: 16 }}
              >
                {jobStatus}
              </Button>
            </Tooltip>
          </Col>
        </Row>

        <Modal
          title={![202, 200].includes(status) && 'Error'}
          visible={showModal}
          onOk={handleClose}
          onCancel={handleClose}
          footer={[
            <Button
              key="refresh"
              type="text"
              shape="circle"
              icon={<ReloadOutlined />}
              onClick={() => handleStatus(jobId)}
              disabled={!jobId}
            />,
            <Button key="submit" type="primary" onClick={handleClose}>
              OK
            </Button>,
          ]}
        >
          <pre>{message}</pre>
        </Modal>
      </div>
    </div>
  );
};

const mapStateToProps = ({ auth }) => ({ ...auth });

export default connect(mapStateToProps)(ImportCSV);
