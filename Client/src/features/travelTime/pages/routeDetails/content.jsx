import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { Card, Alert } from 'antd';
import AverageMetrics, {
  createTransitDelayLabels,
} from '../../../../common/components/AverageMetrics';
import AverageMetricsChart from '../../components/AverageMetricsChart';
import Map from '../../../../common/components/Map';
import { createTravelTimeMarkers, getPaths, createPoints } from './shapes';
import MapIcon from '../../../../common/icons/Map';
import { Metric } from '../../../../common/enums';
import TabView, {
  Header as TabViewHeader,
} from '../../../../common/components/TabView';
import useStats from '../../hooks/useStats';
import useMap from '../../hooks/useMap';
import { metricColorMap } from '../../../../common/constants';
import { createFlags } from '../../../../common/utils/shapes';
import { pluralize } from '../../../../common/utils/string';
import { TooltipText, LOW_CONFIDENCE_THRESHOLD } from '../../constants';
import MapLegend from '../../components/MapLegend';
import './style.css';

const View = {
  Map: 'Map',
};

const ToolTipContent = ({ text, locations, locationType, totalTrips }) => (
  <div>
    <p style={{ marginBottom: '5px' }}>{text}</p>
    {locations.length !== 0 ? (
      <Alert
        style={{ padding: '10px', paddingRight: '2px' }}
        description={
          <>
            <b>
              {locations.length} {pluralize(locationType, locations.length)}
            </b>{' '}
            with {`< 5%`} of {totalTrips} route trips
          </>
        }
        type="warning"
        icon={
          <span role="img">
            <svg
              viewBox="64 64 896 896"
              focusable="false"
              width="1em"
              height="1em"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"></path>
              <path d="M464 688a48 48 0 1096 0 48 48 0 10-96 0zm24-112h48c4.4 0 8-3.6 8-8V296c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8z"></path>

              <g stroke="red" strokeWidth="3" fill="red">
                <circle id="danger" cx="780" cy="200" r="140" />
              </g>
            </svg>
          </span>
        }
        showIcon
      ></Alert>
    ) : null}
  </div>
);

const MapContainer = ({
  isRouteDetailsEmpty,
  direction,
  selectedMetric,
  avgMetrics,
  isLoading,
  selectedMarker,
  onSelectedMarkerChange,
  setIsSelectedRouteOrPointsEmpty,
  totalTrips,
  map,
  stops,
  intersections,
  selectedRoute,
}) => {
  const [bounds, setBounds] = useState();

  const { startDate, endDate } = useSelector(
    ({ routeFilters: { dateRange } }) => dateRange
  );

  // Paths
  const segmentShapes = useMemo(
    () => getPaths(map, selectedMetric, selectedRoute, onSelectedMarkerChange),
    [map, selectedMetric, selectedRoute, onSelectedMarkerChange]
  );

  // Stops/intersections
  const pointShapes = useMemo(() => {
    // Travel time tooltip
    const travelTime = avgMetrics?.traveltime?.mins;

    return selectedMetric === Metric.TravelTime
      ? createTravelTimeMarkers({ travelTime, stops })
      : createPoints({
          metric: selectedMetric,
          stops,
          intersections,
          onClick: onSelectedMarkerChange,
          bounds,
          totalTrips,
        });
  }, [
    avgMetrics?.traveltime?.mins,
    bounds,
    intersections,
    onSelectedMarkerChange,
    selectedMetric,
    stops,
    totalTrips,
  ]);

  // Directional flag
  const flagShapes = useMemo(
    () =>
      createFlags({
        stops,
        direction,
      }),
    [direction, stops]
  );

  // Gather GMaps shapes
  const gmapsShapes = useMemo(
    () => [...flagShapes, ...segmentShapes, ...pointShapes],
    [flagShapes, pointShapes, segmentShapes]
  );

  const isSelectedRouteOrPointsEmpty =
    Object.keys(selectedRoute || {}).length === 0 ||
    Object.keys(gmapsShapes || {}).length === 0;

  useEffect(() => {
    setIsSelectedRouteOrPointsEmpty(isSelectedRouteOrPointsEmpty);
  }, [isSelectedRouteOrPointsEmpty, setIsSelectedRouteOrPointsEmpty]);

  const marker = useCallback(
    (item) => {
      const title = `${item.stopname || item.locationName} (${item.numTrips})`;

      if (item?.periods === undefined) {
        return (
          <Card
            title={title}
            size="small"
            bordered={false}
            style={{ width: 250 }}
          >
            No data is available
          </Card>
        );
      }

      const markerData = Object.keys(item?.periods || {}).map((period) => ({
        value:
          Math.round(
            (parseFloat(item?.periods?.[period]?.[selectedMetric]?.mins) * 60 ||
              0) * 10
          ) / 10,
        change:
          Math.round(item?.periods?.[period]?.[selectedMetric]?.change * 10) /
          10,
      }));

      // Calculate difference in days
      const d = new Date(startDate);
      const d2 = new Date(endDate);
      const numDays = (d2 - d) / (1000 * 60 * 60 * 24);

      return (
        <Card className="map-card" size="medium" bordered={false}>
          <div style={{ width: '45%', float: 'left' }}>
            <h1>{item.stopname || item.locationName}</h1>
            {item.numTrips < totalTrips * LOW_CONFIDENCE_THRESHOLD ? (
              <p style={{ color: '#ff4d4f' }}>* Only {item.numTrips} trips</p>
            ) : (
              <p>{item.numTrips} trips</p>
            )}
          </div>
          <div
            style={{
              width: '20%',
              marginLeft: '4%',
              marginRight: '6%',
              float: 'left',
              textAlign: 'center',
            }}
          >
            <h1>{markerData[1]?.value ? `${markerData[1].value}s` : 'N/A'}</h1>
            <p>
              {startDate.slice(5).replace('-', '/')} -{' '}
              {endDate.slice(5).replace('-', '/')}
            </p>
          </div>
          <div style={{ width: '25%', float: 'left', textAlign: 'center' }}>
            {markerData.length === 1 ? (
              <h1 style={{ color: '#ff4d4f' }}>N/A</h1>
            ) : markerData[1].change > 0 ? (
              <h1 style={{ color: '#52c41a' }}>
                {`+${markerData[1].change}`}s
              </h1>
            ) : (
              <h1 style={{ color: '#ff4d4f' }}>{`${markerData[1].change}`}s</h1>
            )}
            <p>from previous {numDays} days</p>
          </div>
        </Card>
      );
    },
    [selectedMetric, startDate, endDate, totalTrips]
  );

  // Remove the open chart on filter change
  useEffect(() => {
    onSelectedMarkerChange(null);
  }, [stops, intersections, onSelectedMarkerChange]);

  return (
    <>
      <div className="map-container">
        <Map
          isLoading={isLoading}
          isEmpty={isRouteDetailsEmpty}
          selectedMapItemState={[selectedMarker, onSelectedMarkerChange]}
          gmapsShapes={gmapsShapes}
          onViewportBoundsChanged={setBounds}
          tooltips={{ marker }}
        >
          <MapLegend selectedMetric={selectedMetric} />
        </Map>
      </div>
    </>
  );
};

const RouteDetailsContent = ({ match, updateNumTrips }) => {
  const { route } = match.params;

  const [selectedMetric, setSelectedMetric] = useState('signaldelay');
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [view, setView] = useState(View.Map);
  const [isSelectedRouteOrPointsEmpty, setIsSelectedRouteOrPointsEmpty] =
    useState(false);
  const [isRouteDetailsEmpty, setIsRouteDetailsEmpty] = useState(false);

  const { dateRange, direction } = useSelector(
    ({ routeFilters }) => routeFilters
  );

  const { avgMetrics, isLoading: isAvgMetricsLoading } = useStats({
    routeName: route,
  });
  const totalTrips = avgMetrics?.total_trips;

  const totalMins = avgMetrics?.traveltime?.mins;
  const isTotalMinsNaN = Number.isNaN(totalMins);
  const isAvgMetricsEmpty =
    !isAvgMetricsLoading && Object.keys(avgMetrics).length === 0;

  const {
    map,
    stops,
    intersections,
    lowConfidenceStops,
    lowConfidenceIntersections,
    selectedRoute,
    isEmpty: isMapEmpty,
    isLoading: isMapLoading,
  } = useMap({ routeName: route, totalTrips });

  useEffect(() => {
    updateNumTrips(isAvgMetricsLoading ? undefined : totalTrips);
  }, [updateNumTrips, totalTrips, isAvgMetricsLoading]);

  useEffect(() => {
    setIsRouteDetailsEmpty(
      isMapEmpty ||
        isTotalMinsNaN ||
        isAvgMetricsEmpty ||
        isSelectedRouteOrPointsEmpty
    );
  }, [
    isMapEmpty,
    isTotalMinsNaN,
    isAvgMetricsEmpty,
    isSelectedRouteOrPointsEmpty,
  ]);

  const handleSelectedMetricChange = (metric) => {
    setSelectedMetric(metric);
    setSelectedMarker();
  };

  return (
    <section className="route-details">
      <TabView
        views={
          <>
            <MapIcon value={View.Map} />
          </>
        }
        value={view}
        onChange={setView}
        header={
          <TabViewHeader>
            <AverageMetrics
              avgMetrics={isRouteDetailsEmpty ? {} : avgMetrics}
              isLoading={isAvgMetricsLoading || isMapLoading}
              selectedMetric={selectedMetric}
              onSelectedMetricChange={handleSelectedMetricChange}
            >
              <AverageMetrics.Tab
                metric={Metric.SignalDelay}
                tooltip={
                  <ToolTipContent
                    text={TooltipText.SignalDelay}
                    locations={lowConfidenceIntersections}
                    locationType={'intersection'}
                    totalTrips={totalTrips}
                  />
                }
                hasLowConfidenceData={lowConfidenceIntersections.length !== 0}
                style={{
                  borderColor: metricColorMap[Metric.SignalDelay],
                }}
                createLabels={createTransitDelayLabels({
                  totalMins,
                })}
              />
              <span className="route-details__sign">+</span>
              <AverageMetrics.Tab
                metric={Metric.DwellTime}
                tooltip={
                  <ToolTipContent
                    text={TooltipText.DwellTime}
                    locations={lowConfidenceStops}
                    locationType={'stop'}
                    totalTrips={totalTrips}
                  />
                }
                hasLowConfidenceData={lowConfidenceStops.length !== 0}
                style={{
                  borderColor: metricColorMap[Metric.DwellTime],
                }}
                createLabels={createTransitDelayLabels({
                  totalMins,
                })}
              />
              <span className="route-details__sign">+</span>
              <AverageMetrics.Tab
                metric={Metric.DriveTime}
                tooltip={TooltipText.DriveTime}
                style={{
                  borderColor: metricColorMap[Metric.DriveTime],
                }}
                createLabels={createTransitDelayLabels({
                  totalMins,
                })}
              />
              <span className="route-details__sign">=</span>
              <AverageMetrics.Tab
                metric={Metric.TravelTime}
                tooltip={TooltipText.TravelTime}
                style={{
                  borderColor: metricColorMap[Metric.TravelTime],
                }}
                createLabels={createTransitDelayLabels({
                  totalMins,
                })}
              />
            </AverageMetrics>
          </TabViewHeader>
        }
      >
        <>
          {view === View.Map && (
            <MapContainer
              isRouteDetailsEmpty={isRouteDetailsEmpty}
              dateRange={dateRange}
              direction={direction}
              routeName={route}
              selectedMetric={selectedMetric}
              avgMetrics={avgMetrics}
              isLoading={isAvgMetricsLoading || isMapLoading}
              selectedMarker={selectedMarker}
              onSelectedMarkerChange={setSelectedMarker}
              setIsSelectedRouteOrPointsEmpty={setIsSelectedRouteOrPointsEmpty}
              totalTrips={totalTrips}
              map={map}
              stops={stops}
              intersections={intersections}
              selectedRoute={selectedRoute}
            />
          )}
        </>
      </TabView>
      {!isRouteDetailsEmpty && <AverageMetricsChart metric={selectedMetric} />}
    </section>
  );
};

export default withRouter(RouteDetailsContent);
