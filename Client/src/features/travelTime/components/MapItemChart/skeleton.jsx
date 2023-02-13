import { Skeleton } from 'antd';
import 'antd/lib/skeleton/style/css';

const MapItemChartSkeleton = ({ active = false }) => {
  const height = 450;

  return (
    <div>
      <Skeleton.Button
        className="map-item_chart-header_skeleton"
        active={active}
        style={{ height: 60, marginBottom: 4 }}
      />
      <Skeleton.Button
        className="map-item_chart_skeleton"
        active={active}
        style={{ height }}
      />
    </div>
  );
};

export default MapItemChartSkeleton;
