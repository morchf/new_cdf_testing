import React from 'react';
import Breadcrumb from '../../components/Breadcrumb';
import HeadingSection from '../../components/HeadingSection';

const HealthMonitoringLayout = ({
  title,
  subTitle,
  backTo,
  backToLastPath,
  tooltip,
  metricType,
  headerChildren,
  metrics,
  children,
  ...props
}) => (
  <main className="health-monitoring-layout">
    <HeadingSection
      title={title}
      backTo={backTo}
      backToLastPath={backToLastPath}
      subTitle={subTitle}
      tooltip={tooltip}
      above={<Breadcrumb />}
      metrics={metrics}
      {...props}
    >
      {headerChildren}
    </HeadingSection>
    {children}
  </main>
);

export default HealthMonitoringLayout;
