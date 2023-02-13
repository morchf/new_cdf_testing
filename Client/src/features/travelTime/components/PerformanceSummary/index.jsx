import { StarOutlined } from '@ant-design/icons';
import TableCard from '../../../../common/components/TableCard';
import PerformanceTable from '../PerformanceTable';
import Warning from '../../../../common/icons/Warning';
import { TooltipText } from '../../constants';
import './style.css';

const getAvgMetrics = (routes) => {
  let driveTime = 0;
  let dwellTime = 0;
  let travelTime = 0;

  routes.forEach(({ drivetime, dwelltime, traveltime }) => {
    driveTime += +drivetime;
    dwellTime += +dwelltime;
    travelTime += +traveltime;
  });

  const avgDriveTime = driveTime / routes.length;
  const avgDwellTime = dwellTime / routes.length;
  const avgTravelTime = travelTime / routes.length;

  return {
    avgDriveTime,
    avgDwellTime,
    avgTravelTime,
  };
};

const PerformanceSummary = ({ isLoading, performance, routes }) => {
  const avgMetrics = routes ? getAvgMetrics(routes) : [];
  const { topRoutes, worstRoutes } = performance || {};

  return (
    <div className="performance-summary">
      <TableCard
        title="Most Delayed Routes"
        tooltip={TooltipText.Most}
        table={
          <PerformanceTable
            icon={<StarOutlined />}
            isLoading={isLoading}
            routes={worstRoutes}
            avgMetrics={avgMetrics}
            updated={performance?.worstUpdDate}
          />
        }
      />
      <TableCard
        title="Least Delayed Routes"
        tooltip={TooltipText.Least}
        table={
          <PerformanceTable
            icon={<Warning />}
            isLoading={isLoading}
            routes={topRoutes}
            avgMetrics={avgMetrics}
            updated={performance?.topUpdDate}
          />
        }
      />
    </div>
  );
};

export default PerformanceSummary;
