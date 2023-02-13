import { withRouter } from 'react-router-dom';
import { Metric } from '../../../../common/enums';
import AnalyticsLayout from '../../../../common/layouts/AnalyticsLayout';
import ScheduleDeviationStopDetails from './content';

const ScheduleDeviationStopDetailsPage = ({ match }) => {
  const { stop } = match.params;

  return (
    <AnalyticsLayout
      metricType={Metric.ScheduleDeviation}
      backToLastPath
      title={`Stop ${stop}`}
    >
      <ScheduleDeviationStopDetails />
    </AnalyticsLayout>
  );
};

export default withRouter(ScheduleDeviationStopDetailsPage);
