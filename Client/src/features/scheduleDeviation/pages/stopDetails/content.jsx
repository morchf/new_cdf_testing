import { useEffect, useState } from 'react';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import TabView, {
  Header as TabViewHeader,
} from '../../../../common/components/TabView';
import MapIcon from '../../../../common/icons/Map';
import AverageMetrics, {
  createScheduleDeviationLabels,
} from '../../../../common/components/AverageMetrics';
import Map from '../../../../common/components/Map';
import { getIconStop } from './shapes';
import { LatenessPointTooltip } from '../../components/MapTooltips';
import { Metric } from '../../../../common/enums';
import TimeframeLineChartForStop from '../../components/TimeframeLineChartForStop';
import TimeframeColumnChartForStop from '../../components/TimeframeColumnChartForStop';
import useStop from '../../hooks/useStop';
import { setSelectedMetric } from '../../store/slice';
import { metricColorMap } from '../../../../common/constants';
import './style.css';

const View = {
  Map: 'Map',
};

const ScheduleDeviationStopDetails = ({
  dateRange,
  match,
  selectedMetric,
  onSelectedMetricChange,
}) => {
  const { stop: stopName, route: routeName } = match.params;

  const [view, setView] = useState(View.Map);
  const [selectedMarker, setSelectedMarker] = useState(null);

  const { stop, avgMetrics, isLoading } = useStop({ routeName, stopName });

  // Reset the selected metric on page change
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => () => onSelectedMetricChange(selectedMetric), []);

  const handleSelectedMetricChange = (metric) => {
    onSelectedMetricChange(metric);
    setSelectedMarker();
  };

  // Create Google Map icon from stop
  const icon = getIconStop(stop, setSelectedMarker);
  const gmapsShapes = icon ? [icon] : [];

  return (
    <section className="schedule-deviation-stop-details">
      <TabView
        className="schedule-deviation-stop-details__tabs"
        value={view}
        onChange={setView}
        header={
          <TabViewHeader>
            <AverageMetrics
              avgMetrics={avgMetrics}
              numMetrics={2}
              isLoading={isLoading}
              selectedMetric={selectedMetric}
              onSelectedMetricChange={handleSelectedMetricChange}
            >
              <AverageMetrics.Tab
                metric={Metric.OnTimePercentage}
                style={{
                  borderColor: metricColorMap[Metric.OnTimePercentage],
                }}
                createLabels={createScheduleDeviationLabels({ dateRange })}
              />
              <AverageMetrics.Tab
                metric={Metric.ScheduleDeviation}
                style={{
                  borderColor: metricColorMap[Metric.ScheduleDeviation],
                }}
                createLabels={createScheduleDeviationLabels({ dateRange })}
              />
            </AverageMetrics>
          </TabViewHeader>
        }
        views={
          <>
            <MapIcon value={View.Map} />
          </>
        }
      >
        {view === View.Map && (
          <Map
            isLoading={isLoading}
            selectedMapItemState={[selectedMarker, setSelectedMarker]}
            gmapsShapes={gmapsShapes}
            tooltips={{
              marker: (item) => <LatenessPointTooltip item={item} />,
            }}
          />
        )}
      </TabView>

      {selectedMetric === Metric.ScheduleDeviation && (
        <TimeframeLineChartForStop dateRange={dateRange} />
      )}
      {selectedMetric === Metric.OnTimePercentage && (
        <TimeframeColumnChartForStop dateRange={dateRange} />
      )}
    </section>
  );
};

const mapStateToProps = ({ scheduleDeviation, routeFilters }) => {
  const { dateRange } = routeFilters;
  const { selectedMetric } = scheduleDeviation;

  return {
    dateRange,
    selectedMetric,
  };
};

const mapDispatchToProps = {
  onSelectedMetricChange: (selectedMetric) => async (dispatch) =>
    dispatch(setSelectedMetric(selectedMetric)),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withRouter(ScheduleDeviationStopDetails));
