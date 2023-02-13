import React, { memo } from 'react';
import { withRouter } from 'react-router-dom';
import Breadcrumb from '../../components/Breadcrumb';
import HeadingSection from '../../components/HeadingSection';
import './style.css';

const ConfigurationLayout = ({
  children,
  match,
  backToLastPath = false,
  ...props
}) => {
  const { regname, agyname, vehname, devname, intersectionName } = match.params;

  return (
    <main className="configuration-layout">
      <HeadingSection
        backToLastPath={backToLastPath}
        above={
          <Breadcrumb.Config
            regionName={regname}
            agencyName={agyname}
            vehicleName={vehname}
            deviceName={devname}
            intersectionName={intersectionName}
          />
        }
        {...props}
      />
      {children}
    </main>
  );
};

export default memo(withRouter(ConfigurationLayout));
