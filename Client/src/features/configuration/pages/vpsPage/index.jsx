import React from 'react';
import { useSelector } from 'react-redux';
import ConfigurationLayout from '../../../../common/layouts/ConfigurationLayout';
import VPSContent from './content';
import { capitalizeFirstLetter } from '../../utils';

const VPSPage = () => {
  const agyname = useSelector((state) => state.user.agency);
  const capAgyname = capitalizeFirstLetter(agyname);

  return (
    <ConfigurationLayout>
      <VPSContent agyname={agyname} />
    </ConfigurationLayout>
  );
};

export default VPSPage;
