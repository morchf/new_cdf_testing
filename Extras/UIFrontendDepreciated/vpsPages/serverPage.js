import React from 'react';
import ServerTable from './serverTable';
import ImportCSV from './importCSV';
import Provision from './provision';

const ServerPage = (props) => {
  const items = props;
  return (
    <div
      style={{
        marginTop: '3%',
      }}
    >
      <div className="ServerPage">
        <h1>{items.customerName ? items.customerName : 'ServerPage'}</h1>
        <ServerTable customerName={items.customerName} vpss={items.vpss} />
        <Provision customerName={items.customerName} />
        <ImportCSV />
      </div>
    </div>
  );
};

export default ServerPage;
