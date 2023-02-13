import { Skeleton } from 'antd';
import 'antd/lib/skeleton/style/css';

const RouteNamesListSkeleton = ({ active = false }) => {
  const width = 300;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: 140,
      }}
    >
      <Skeleton.Button active={active} style={{ width }} size="small" />
      <Skeleton.Button active={active} style={{ width }} size="small" />
      <Skeleton.Button active={active} style={{ width }} size="small" />
      <Skeleton.Button active={active} style={{ width }} size="small" />
    </div>
  );
};

export default RouteNamesListSkeleton;
