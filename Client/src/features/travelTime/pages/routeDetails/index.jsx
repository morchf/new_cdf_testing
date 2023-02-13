import React, { useState, useCallback } from 'react';
import { withRouter } from 'react-router-dom';
import { Metric } from '../../../../common/enums';
import AnalyticsLayout from '../../../../common/layouts/AnalyticsLayout';
import RouteDetailsContent from './content';

const RouteDetailsPage = ({ match }) => {
  const { route: routeName } = match.params;
  const [numTrips, setNumTrips] = useState(undefined);

  const updateNumTrips = useCallback(
    (trips) => setNumTrips(trips),
    [setNumTrips]
  );

  return (
    <AnalyticsLayout
      metricType={Metric.TravelTime}
      backTo="/analytics/transit-delay"
      title={`Route ${routeName} ${
        numTrips !== undefined ? `(${numTrips} trips)` : ''
      }`}
    >
      <RouteDetailsContent updateNumTrips={updateNumTrips} />
    </AnalyticsLayout>
  );
};

export default withRouter(RouteDetailsPage);
