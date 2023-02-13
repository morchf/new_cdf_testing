import { Skeleton } from 'antd';
import 'antd/lib/skeleton/style/css';
import './style.css';

const AvgMetricsSkeleton = ({ number, active = false }) => (
  <>
    {new Array(number).fill().map((_, index) => (
      <Skeleton.Button
        className="avg-metrics-skeleton__button"
        key={index}
        active={active}
      />
    ))}
  </>
);

export default AvgMetricsSkeleton;
