import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { capitalize1stLetter } from '../../../common/utils';
import { joinMetricsSegments } from '../pages/routeDetails/shapes';
import usePoints from './usePoints';
import useRoutes from './useRoutes';

const useMap = ({ routeName }) => {
  const { selectedRoute, isLoading: isMapLoading } = useRoutes({
    routeName,
  });
  const { latenessPoints, isLoading: isLatenessPointsLoading } = usePoints({
    routeName,
  });

  const stopsWithMetrics = useMemo(
    () =>
      joinMetricsSegments(selectedRoute?.segments, latenessPoints)
        .map(
          ({ ontimepercentage, latepercentage, earlypercentage, ...rest }) => ({
            onTimePercentage: ontimepercentage?.percent * 100,
            earlyPercentage: earlypercentage?.percent * 100,
            latePercentage: latepercentage?.percent * 100,
            ontimepercentage,
            latepercentage,
            earlypercentage,
            ...rest,
          })
        )
        .sort((s1, s2) => {
          if (s1.direction !== s2.direction)
            return s2.direction.localeCompare(s1.direction);
          return +s1.stoporder - +s2.stoporder;
        })
        .map(
          ({
            stopname,
            stoporder,
            stopNumber,
            direction: stopDirection,
            ...rest
          }) => ({
            stoporder,
            stopname: `${stopname} (${capitalize1stLetter(
              stopDirection
            )} #${stopNumber})`,
            stopNumber,
            stopNameShort: stopname,
            direction: stopDirection,
            ...rest,
          })
        ),
    [latenessPoints, selectedRoute?.segments]
  );

  const isEmpty = useMemo(
    () =>
      Object.keys(selectedRoute || {}).length === 0 ||
      Object.keys(latenessPoints || {}).length === 0,
    [latenessPoints, selectedRoute]
  );

  const isLoading = useMemo(
    () => isMapLoading || isLatenessPointsLoading,
    [isLatenessPointsLoading, isMapLoading]
  );

  return {
    selectedRoute,
    stops: stopsWithMetrics,
    isLoading,
    isEmpty,
  };
};

export default useMap;
