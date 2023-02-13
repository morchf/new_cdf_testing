import { useEffect, useMemo, useState } from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { LatenessPointTooltip } from '../../components/MapTooltips';
import Map from '../../../../common/components/Map';
import TabView, {
  Header as TabViewHeader,
} from '../../../../common/components/TabView';
import MapIcon from '../../../../common/icons/Map';
import { getPaths, createPoints } from './shapes';
import AverageMetrics, {
  createScheduleDeviationLabels,
} from '../../../../common/components/AverageMetrics';
import { Metric } from '../../../../common/enums';
import { setSelectedMetric } from '../../store/slice';
import { metricColorMap } from '../../../../common/constants';
import useAvgMetrics from '../../hooks/useAvgMetrics';
import { createFlags } from '../../../../common/utils/shapes';
import StopsTimeframeColumnCharts from '../../components/StopsTimeframeColumnCharts';
import StopsTimeframeLineCharts from '../../components/StopsTimeframeLineCharts';
import { TooltipText } from '../../constants';
import useMap from '../../hooks/useMap';
import './style.css';

const View = {
  Map: 'Map',
};

const AverageMetricsContainer = ({
  avgMetrics,
  isAvgMetricsLoading,
  selectedMetric,
  onSelectedMetricChange,
  dateRange,
}) => (
  <AverageMetrics
    avgMetrics={avgMetrics}
    numMetrics={2}
    isLoading={isAvgMetricsLoading}
    selectedMetric={selectedMetric}
    onSelectedMetricChange={onSelectedMetricChange}
  >
    <AverageMetrics.Tab
      metric={Metric.OnTimePercentage}
      tooltip={TooltipText.OnTimePercentage}
      style={{
        borderColor: metricColorMap[Metric.OnTimePercentage],
      }}
      createLabels={createScheduleDeviationLabels({ dateRange })}
    />
    <AverageMetrics.Tab
      metric={Metric.ScheduleDeviation}
      tooltip={TooltipText.ScheduleDeviation}
      style={{
        borderColor: metricColorMap[Metric.ScheduleDeviation],
      }}
      createLabels={createScheduleDeviationLabels({ dateRange })}
    />
  </AverageMetrics>
);

const MapContainer = ({
  isRouteDetailsEmpty,
  selectedMarker,
  onSelectedMarkerChange,
  route,
  direction,
  color,
  metric,
  setIsMapEmpty,
  setIsMapLoading,
}) => {
  const [bounds, setBounds] = useState();

  const {
    selectedRoute,
    stops,
    isLoading,
    isEmpty: isMapEmpty,
  } = useMap({
    routeName: route,
  });

  const segmentShapes = useMemo(
    () => getPaths(selectedRoute, color),
    [color, selectedRoute]
  );

  const pointShapes = useMemo(
    () =>
      createPoints({
        stops: Object.values(stops || {}),
        onClick: onSelectedMarkerChange,
        bounds,
        metric,
      }),
    [bounds, metric, onSelectedMarkerChange, stops]
  );

  const flagShapes = useMemo(
    () =>
      createFlags({
        stops,
        direction,
      }),
    [stops, direction]
  );

  const gmapsShapes = useMemo(
    () => [...segmentShapes, ...pointShapes, ...flagShapes],
    [flagShapes, pointShapes, segmentShapes]
  );

  const isEmpty = useMemo(
    () => isMapEmpty || Object.keys(gmapsShapes || {}).length === 0,
    [isMapEmpty, gmapsShapes]
  );

  useEffect(() => {
    setIsMapLoading(isLoading);
    setIsMapEmpty(!isLoading && isEmpty);
  }, [isLoading, isEmpty, setIsMapLoading, setIsMapEmpty]);

  // Remove the open chart on filter change
  useEffect(() => {
    onSelectedMarkerChange(null);
  }, [stops, onSelectedMarkerChange]);

  return (
    <div className="map-container">
      <Map
        isLoading={isLoading}
        isEmpty={isEmpty || isRouteDetailsEmpty}
        selectedMapItemState={[selectedMarker, onSelectedMarkerChange]}
        onViewportBoundsChanged={setBounds}
        gmapsShapes={gmapsShapes}
        tooltips={{
          // temporarily disabled the link to L3 page
          marker: (item) => (
            <LatenessPointTooltip isLink={false} item={item} metric={metric} />
          ),
        }}
      />
    </div>
  );
};

const ScheduleDeviationRouteDetails = ({
  match,
  filters,
  selectedMetric,
  onSelectedMetricChange = () => {},
}) => {
  const { route } = match.params;
  const { dateRange, direction } = filters;

  const [view, setView] = useState(View.Map);
  const [selectedMarker, setSelectedMarker] = useState();
  const [isMapEmpty, setIsMapEmpty] = useState(false);
  const [isRouteDetailsEmpty, setIsRouteDetailsEmpty] = useState(false);
  const [isMapLoading, setIsMapLoading] = useState(true);

  const { avgMetrics, isLoading: isAvgMetricsLoading } = useAvgMetrics({
    routeName: route,
  });
  const isAvgMetricsEmpty =
    !isAvgMetricsLoading &&
    (!avgMetrics || Object.keys(avgMetrics).length === 0);

  // Scroll to map
  useEffect(() => {
    const map = document.querySelector('.map-container');

    if (!map) return;

    const mapYOffset = map.offsetTop;
    const navbarHeight = document.querySelector(
      'header.ant-layout-header'
    ).offsetHeight;

    window.scrollTo({
      top: mapYOffset - navbarHeight - 4,
      behavior: 'smooth',
    });
  }, []);

  const handleSelectedMetricChange = (metric) => {
    onSelectedMetricChange(metric);
    setSelectedMarker();
  };

  useEffect(() => {
    setIsRouteDetailsEmpty(isMapEmpty || isAvgMetricsEmpty);
  }, [isMapEmpty, isAvgMetricsEmpty]);

  return (
    <div className="schedule-deviation-route-details">
      <TabView
        value={view}
        onChange={setView}
        header={
          <TabViewHeader>
            <AverageMetricsContainer
              avgMetrics={isRouteDetailsEmpty ? {} : avgMetrics}
              isAvgMetricsLoading={isAvgMetricsLoading || isMapLoading}
              selectedMetric={selectedMetric}
              onSelectedMetricChange={handleSelectedMetricChange}
              dateRange={dateRange}
            />
          </TabViewHeader>
        }
        views={
          <>
            <MapIcon value={View.Map} />
          </>
        }
      >
        {view === View.Map && (
          <MapContainer
            isRouteDetailsEmpty={isRouteDetailsEmpty}
            route={route}
            direction={direction}
            color={metricColorMap[selectedMetric]}
            metric={selectedMetric}
            selectedMarker={selectedMarker}
            onSelectedMarkerChange={setSelectedMarker}
            setIsMapEmpty={setIsMapEmpty}
            setIsMapLoading={setIsMapLoading}
          />
        )}
      </TabView>

      {!isRouteDetailsEmpty && selectedMetric === Metric.OnTimePercentage && (
        <StopsTimeframeColumnCharts
          dateRange={dateRange}
          routeName={route}
          direction={direction}
        />
      )}

      {!isRouteDetailsEmpty && selectedMetric === Metric.ScheduleDeviation && (
        <StopsTimeframeLineCharts routeName={route} />
      )}
    </div>
  );
};

const mapStateToProps = ({ scheduleDeviation, routeFilters }) => {
  const { selectedMetric } = scheduleDeviation;

  return {
    filters: routeFilters,
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
)(withRouter(ScheduleDeviationRouteDetails));
