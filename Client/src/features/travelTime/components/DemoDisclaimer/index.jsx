import { Modal } from 'antd';
import { connect } from 'react-redux';
import { useEffect, useState } from 'react';

// Used to display a Modal explaining the disclaimer for demo agency
const DemoDisclaimer = ({ agency }) => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const handleConfirm = () => {
    setIsModalVisible(false);
  };
  // Need to display demo disclaimer in pilot environment irrespective of agency, in other environments it should display only for demo agency
  useEffect(() => {
    const disclaimerCount = sessionStorage.getItem('disclaimerCount', '0');
    if (
      disclaimerCount !== '1' &&
      (agency === 'demo' ||
        process.env.REACT_APP_SC_DOMAIN_NAME === 'cdfmanager-pilot')
    ) {
      setIsModalVisible(true);
      sessionStorage.setItem('disclaimerCount', '1');
    }
  }, [agency]);
  return (
    <div>
      <Modal
        title="THIS IS A DEMO ENVIRONMENT. ALL DATA PREVIEWED IS MANUFACTURED AND PLACED ON A REAL LOCATION MAP TO SHOW THE PRODUCT FEATURES AND REPORTS."
        visible={isModalVisible}
        onOk={handleConfirm}
        okText="Confirm"
        cancelButtonProps={{ style: { display: 'none' } }}
        closable={false}
        keyboard={false}
      >
        <p>
          This demonstration data is not reflective of the City of San
          Francisco&apos;s actual routes and data.
        </p>
      </Modal>
    </div>
  );
};

const mapStateToProps = ({ user }) => {
  const { agency } = user;
  return { agency };
};

export default connect(mapStateToProps)(DemoDisclaimer);
