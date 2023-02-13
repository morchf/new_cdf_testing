import 'ol/ol.css';
import {
  Circle,
  Stroke,
  Style,
  Fill,
} from 'ol/style';

const getBusStopStyle = (lateness = null) => new Style({
  image: new Circle({
    radius: 4,
    fill: new Fill({
      color: 'rgba(255, 255, 255, 0.4)',
    }),
    stroke: new Stroke({
      color: 'rgb(25, 25, 25)',
      width: 2,
    }),
  }),
});

const getMultiLineStringOutlineStyle = () => new Style({
  stroke: new Stroke({
    color: 'rgb(145, 145, 145)',
    width: 6,
  }),
});

const getMultiLineStringStyle = (color) => new Style({
  stroke: new Stroke({
    color,
    width: 4,
  }),
});

const getStartPointStyle = (color) => new Style({
  image: new Circle({
    radius: 7,
    fill: new Fill({
      color: 'rgb(25, 25, 25)',
    }),
    stroke: new Stroke({
      color,
      width: 4,
    }),
  }),
});

const getEndPointStyle = (color) => new Style({
  image: new Circle({
    radius: 7,
    fill: new Fill({
      color,
    }),
    stroke: new Stroke({
      color: 'rgb(25, 25, 25)',
      width: 4,
    }),
  }),
});

const getLatenessPointStyle = (lateness = null, max) => {
  const minRadius = 4;
  const maxRadius = 10;

  const relSize = Math.abs(lateness / max);
  const radius = minRadius + relSize * (maxRadius - minRadius);
  const isOverZero = lateness > 0;

  return new Style({
    image: new Circle({
      radius,
      fill: new Fill({
        color: isOverZero ? '#EB2D3E' : '#21EB50',
      }),
      stroke: new Stroke({
        color: '#1890FF',
        width: 2,
      }),
    }),
  })
};

const getRouteStyle = (color = 'green') => ({
  multiLineStringOutlineStyle: getMultiLineStringOutlineStyle(),
  multiLineStringStyle: getMultiLineStringStyle(color),
  startStyle: getStartPointStyle(color),
  endStyle: getEndPointStyle(color),
});

export {
  getBusStopStyle,
  getLatenessPointStyle,
  getRouteStyle,
};
