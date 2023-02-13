import React from 'react';
import Breadcrumb from '../../components/Breadcrumb';
import Filters from '../../components/Filters';
import HeadingSection from '../../components/HeadingSection';
import useAgency from '../../hooks/useAgency';
import useAgencyDefaults from '../../hooks/useAgencyDefaults';

const AnalyticsLayout = ({
  title,
  subTitle,
  backTo,
  backToLastPath,
  tooltip,
  metricType,
  children,
  ...props
}) => {
  const {
    status: { availability },
    isLoading,
  } = useAgency();

  const { agencyGuid, agencyPeriods } = useAgencyDefaults();

  return (
    <main className="analytics-layout">
      <HeadingSection
        title={title}
        backTo={backTo}
        backToLastPath={backToLastPath}
        subTitle={subTitle}
        tooltip={tooltip}
        above={<Breadcrumb />}
        {...props}
      >
        <Filters
          isLoading={isLoading}
          availability={availability[metricType]}
          isPeriodSingleSelect={true}
          agencyPeriods={agencyPeriods}
        />
      </HeadingSection>
      {children}
    </main>
  );
};

export default AnalyticsLayout;
