import React from 'react';
import ServerTable from '../../components/ServerTable';
import ConfigCMS from '../../components/ConfigCMS';
import Provision from '../../components/Provision';

const VPSContent = ({ agyname }) => (
  <div className="VPSPage">
    <ServerTable agyname={agyname} />
    <Provision customerName={agyname} />
    <ConfigCMS />
  </div>
);

export default VPSContent;
