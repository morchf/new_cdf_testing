import React from 'react';
import { withRouter } from 'react-router-dom';
import { Metric } from '../../../../common/enums';
import AnalyticsLayout from '../../../../common/layouts/AnalyticsLayout';
import ScheduleDeviationContent from './content';

const ScheduleDeviationRouteDetailsPage = ({ match }) => {
  const { route: routeName } = match.params;

  return (
    <AnalyticsLayout
      metricType={Metric.ScheduleDeviation}
      backTo="/analytics/schedule-deviation"
      title={`Route ${routeName}`}
    >
      <ScheduleDeviationContent />
    </AnalyticsLayout>
  );
};

export default withRouter(ScheduleDeviationRouteDetailsPage);
