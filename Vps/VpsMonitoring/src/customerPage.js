import React from 'react';
import CustomerBarchart from './customerBarchart';
import CustomerTable from './customerTable';

const CustomerPage = (props) => {
  const items = props;
  return (
    <div className="CustomerPage">
      <div
        style={{
          marginTop: '1%',
        }}
      >
        <h1>Customer Page</h1>
        <CustomerTable vpss={items.vpss} />
      </div>
    </div>
  );
};

export default CustomerPage;
