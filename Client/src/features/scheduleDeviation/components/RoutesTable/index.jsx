import React, { useEffect, useMemo, useState } from 'react';
import { connect, useSelector } from 'react-redux';
import RelativeLink from '../../../../common/components/RelativeLink';
import Table from '../../../../common/components/Table';
import TableCard from '../../../../common/components/TableCard';
import TableSearch from '../../../../common/components/TableSearch';
import useRoutesSearchKeysFilter from '../../../../common/hooks/useRoutesSearchKeysFilter';
import {
  convertRelativeToPercentages,
  humanizeDeviationLabel,
} from '../../../../common/utils';
import {
  filterItemsWithRouteFilters,
  getRouteDeviationLabel,
} from '../../utils';
import { setSelectedRoutes } from '../../store/slice';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../../featurePersistence/store/selectors';

const convertPercentages = (data = []) =>
  data.map(
    ({
      onTimePercentage: onTime,
      earlyPercentage: early,
      latePercentage: late,
      ...rest
    }) => {
      const [onTimePercentage, earlyPercentage, latePercentage] =
        convertRelativeToPercentages([onTime, early, late]);
      return {
        onTimePercentage,
        earlyPercentage,
        latePercentage,
        ...rest,
      };
    }
  );

const comparePercentages = (a, b) => {
  if (a == null) return -1;
  if (b == null) return 1;

  return +a.slice(0, -1) - +b.slice(0, -1);
};

const RoutesTable = ({
  latenessRoutes,
  dataSource,
  filters,
  onSelectedRoutesChange = () => {},
  ...props
}) => {
  const [searchKeys, setSearchKeys] = useState([]);

  const formattedData = useMemo(
    () => convertPercentages(dataSource),
    [dataSource]
  );

  // Filter with search keys and filters (deviation category / selected time)
  const searchKeysFiltered = useRoutesSearchKeysFilter(
    searchKeys,
    formattedData
  );
  const onTimeRange = useSelector(selectTimeRange);
  const data = filterItemsWithRouteFilters(
    filters,
    onTimeRange
  )(searchKeysFiltered);

  // Reset selected keys if filters are changed
  useEffect(() => {
    setSearchKeys([]);
  }, [filters]);

  const routesTableHeader = [
    {
      title: 'Route Name',
      dataIndex: 'route',
      key: 'route',
      sorter: (a, b) =>
        a.route.localeCompare(
          b.route,
          navigator.languages[0] || navigator.language,
          { numeric: true, ignorePunctuation: true }
        ),
      sortDirections: ['ascend', 'descend'],
      render: (routeName) => (
        <RelativeLink key={routeName} to={routeName} className="btn-analytics">
          {`Route ${routeName}`}
        </RelativeLink>
      ),
    },
    {
      title: '% On-time Arrivals',
      dataIndex: 'onTimePercentage',
      key: 'onTimePercentage',
      defaultSortOrder: 'descend',
      sorter: (a, b) =>
        comparePercentages(a.onTimePercentage, b.onTimePercentage),
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: '% Early Arrivals',
      dataIndex: 'earlyPercentage',
      key: 'earlyPercentage',
      sorter: (a, b) =>
        comparePercentages(a.earlyPercentage, b.earlyPercentage),
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: '% Late Arrivals',
      dataIndex: 'latePercentage',
      key: 'latePercentage',
      sorter: (a, b) => comparePercentages(a.latePercentage, b.latePercentage),
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: 'Average Schedule Deviation',
      dataIndex: 'avgScheduleDeviation',
      key: 'avgScheduleDeviation',
      render: humanizeDeviationLabel,
      sorter: (a, b) =>
        parseFloat(a.avgScheduleDeviation) - parseFloat(b.avgScheduleDeviation),
      sortDirections: ['ascend', 'descend'],
    },
  ];

  const title = getRouteDeviationLabel(filters, onTimeRange);

  return (
    <TableCard
      title={title}
      controls={
        <>
          {props.isLoading || (
            <TableSearch
              data={dataSource}
              handleSearch={setSearchKeys}
              itemSearchField="route"
              searchKeys={searchKeys}
              placeholder="Enter Route"
              title="Search Routes:"
            />
          )}
        </>
      }
      table={
        <Table
          {...props}
          columns={routesTableHeader}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          dataSource={data}
          rowKey={(record) => `${record.route}-${record.direction}`}
        />
      }
      {...props}
    />
  );
};

const mapStateToProps = ({ scheduleDeviation, routeFilters }) => {
  const { latenessRoutes, filters } = scheduleDeviation;

  return {
    latenessRoutes,
    filters: {
      ...filters,
      ...routeFilters,
    },
  };
};

const mapDispatchToProps = {
  onSelectedRoutesChange: (selectedRoutes) => (dispatch) =>
    dispatch(setSelectedRoutes(selectedRoutes)),
};

export default connect(mapStateToProps, mapDispatchToProps)(RoutesTable);
