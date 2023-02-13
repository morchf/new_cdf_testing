import { Skeleton } from 'antd';
import 'antd/lib/skeleton/style/css';
import './style.css';

const TableSkeleton = ({ active = false }) => (
  <div className="table-skeleton">
    <Skeleton.Button active={active} style={{ height: 50, width: '100%' }} />
    <Skeleton.Button active={active} style={{ height: 160, width: '100%' }} />
  </div>
);

export default TableSkeleton;
