import React from 'react';
import AnalyticsLayout from '../../../../common/layouts/AnalyticsLayout';
import OverviewContent from './content';
import { TooltipText } from '../../constants';
import DemoDisclaimer from '../../components/DemoDisclaimer';
import { Metric } from '../../../../common/enums';

const OverviewPage = () => (
  <AnalyticsLayout
    metricType={Metric.TravelTime}
    title="Transit Delay"
    tooltip={TooltipText.Heading}
  >
    <DemoDisclaimer />
    <OverviewContent />
  </AnalyticsLayout>
);

export default OverviewPage;
