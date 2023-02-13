import React from 'react';
import AnalyticsLayout from '../../../../common/layouts/AnalyticsLayout';
import ScheduleDeviationContent from './content';
import { TooltipText } from '../../constants';
import DemoDisclaimer from '../../../travelTime/components/DemoDisclaimer';
import { Metric } from '../../../../common/enums';

const ScheduleDeviationPage = () => (
  <AnalyticsLayout
    metricType={Metric.ScheduleDeviation}
    title="Schedule Deviation"
    tooltip={TooltipText.Heading}
  >
    <DemoDisclaimer />
    <ScheduleDeviationContent />
  </AnalyticsLayout>
);

export default ScheduleDeviationPage;
