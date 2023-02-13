import React, { useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import { DotChartOutlined } from '@ant-design/icons';
import { connect, useDispatch, useSelector } from 'react-redux';
import OverallCard from '../../components/OverallCard';
import PerformanceTable from '../../components/PerformanceTable';
import RoutesTable from '../../components/RoutesTable';
import TabView from '../../../../common/components/TabView';
import DeviationCategoryGraph from '../../components/DeviationCategoryGraph';
import { setSelectedRoutes } from '../../store/slice';
import useOverview from '../../hooks/useOverview';
import './style.css';
import { TooltipText } from '../../constants';
import openNotification from '../../../../common/components/notification';
import { ERROR_NOT_SETUP, ERROR_NO_DATA } from '../../../../common/constants';
import useAgency from '../../../../common/hooks/useAgency';
import { Metric } from '../../../../common/enums';
import {
  selectTimeperiod,
  selectTimeRange,
} from '../../../featurePersistence/store/selectors';
import {
  setTimeperiod,
  setOnTimeRange,
} from '../../../featurePersistence/store/slice';
import useFeaturePersistence from '../../../featurePersistence/hooks/useFeaturePersistence';
import { selectAgencyGuid } from '../../../userAuth/store/selectors';

const View = {
  Graph: 'Graph',
};

const ScheduleDeviationContent = ({
  filters,
  onTimeRange,
  onSelectedRoutesChange = () => {},
}) => {
  const [view, setView] = useState(View.Graph);
  const [noData, setNoData] = useState(false);

  const {
    agency: agencyData,
    isLoading: agencyLoading,
    isError: agencyConfigError,
    error: agencyInfoError,
    editFeaturePersistanceTSPResponse,
    editFeaturePersistanceTSP,
  } = useFeaturePersistence();
  const { dateRange, direction, periods } = filters;
  const agencyGuid = useSelector(selectAgencyGuid);
  const dispatch = useDispatch();
  useEffect(() => {
    if (!agencyLoading && !agencyConfigError && 'Feature' in agencyData) {
      const timeperiodData = [
        {
          start_time: agencyData.Feature.peak_am_range.start_time,
          label: 'peak_am',
          end_time: agencyData.Feature.peak_am_range.end_time,
        },
        {
          start_time: agencyData.Feature.peak_pm_range.start_time,
          label: 'peak_pm',
          end_time: agencyData.Feature.peak_pm_range.end_time,
        },
      ];
      const onTimeData = [
        agencyData.Feature.late_schedule_deviation_limit,
        agencyData.Feature.early_schedule_deviation_limit,
      ];
      dispatch(setTimeperiod(timeperiodData));
      dispatch(setOnTimeRange(onTimeData));
    }
  }, [agencyLoading, agencyData, dispatch, agencyConfigError]);

  const { overview, table, isLoading } = useOverview();
  const { top, worst } = overview;
  const {
    status: { availability },
    isLoading: isStatusLoading,
  } = useAgency();

  // Check if any date range is available
  useEffect(() => {
    if (isStatusLoading || availability[Metric.ScheduleDeviation].isAvailable) {
      return;
    }

    setNoData(true);
    openNotification({
      message: 'Error 404',
      description: ERROR_NOT_SETUP,
    });
  }, [availability, isStatusLoading]);

  // Check if any data is available in date range
  useEffect(() => {
    if (!isLoading && availability[Metric.ScheduleDeviation].isAvailable)
      if (
        (table && table.length === 0) ||
        (overview && Object.keys(overview).length === 0)
      ) {
        setNoData(true);
        openNotification({
          message: 'Error 404',
          description: ERROR_NO_DATA,
        });
      } else setNoData(false);
  }, [table, overview, isLoading, availability]);

  return (
    <div className="ScheduleDevOverviewPage">
      <OverallCard
        noData={noData}
        early={overview?.overall?.early}
        isLoading={isLoading}
        late={overview?.overall?.late}
        onTime={overview?.overall?.onTime}
        tooltip={TooltipText.Overall}
      />
      <PerformanceTable
        className="mostOntimeSec"
        isLoading={isLoading}
        summaryCategory={top}
        title="Most On-time Routes"
        tooltip={TooltipText.Most}
      />
      <PerformanceTable
        className="leastOntimeSec"
        isLoading={isLoading}
        summaryCategory={worst}
        title="Least On-time Routes"
        tooltip={TooltipText.Least}
      />

      <TabView
        value={view}
        onChange={setView}
        views={
          <>
            <DotChartOutlined value={View.Graph} />
          </>
        }
      >
        {view === View.Graph && (
          <DeviationCategoryGraph chart={table} isLoading={isLoading} />
        )}
      </TabView>

      {view === View.Graph && (
        <RoutesTable
          className="ScheduleDevOverviewPage__table"
          dataSource={table}
          isLoading={isLoading}
          setSelectedRoutes={onSelectedRoutesChange}
        />
      )}
    </div>
  );
};

const mapStateToProps = ({ routeFilters }) => ({ filters: routeFilters });

const mapDispatchToProps = {
  onSelectedRoutesChange: (selectedRoutes) => async (dispatch) =>
    dispatch(setSelectedRoutes(selectedRoutes)),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withRouter(ScheduleDeviationContent));
