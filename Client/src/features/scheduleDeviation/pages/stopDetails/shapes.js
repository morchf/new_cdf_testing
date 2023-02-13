import { getMarker } from '../../../../common/components/Map/GMaps/drawShapes';
import BusStopSVG from '../../../../common/icons/BusStop.svg';

// eslint-disable-next-line import/prefer-default-export
export const getIconStop = (stop, setSelectedMarker) => {
  if (!stop) return null;
  return getMarker(
    stop,
    setSelectedMarker,
    {
      url: BusStopSVG,
      // Half the height/width of the BusStopSVG
      anchor: { x: 10, y: 10 },
    },
    stop.stopname
  );
};
