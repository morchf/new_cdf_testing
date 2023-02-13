import { Skeleton } from 'antd';
import 'antd/lib/skeleton/style/css';
import './style.css';

const OverallCardSkeleton = ({ active = false }) => {
  const height = 140;

  return <Skeleton.Button active={active} style={{ height }} />;
};

export default OverallCardSkeleton;
