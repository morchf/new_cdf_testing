import React, { useEffect, useRef, useState } from 'react';
import TileLayer from 'ol/layer/Tile';
import OSMSource from 'ol/source/OSM';
import OLMap from 'ol/Map';
import View from 'ol/View';
import { Vector as VectorLayer } from 'ol/layer';
import { Vector as VectorSource } from 'ol/source';
// import GoogleLayer from 'olgm/layer/Google';
// import OLGoogleMaps from 'olgm/OLGoogleMaps';
import { latLonToMercator } from './drawShapes';
import {
  extractFeatureWithTooltip,
  findVectorLayer,
  fitMap,
  removeOverlayElementIfAny,
  setupTooltip,
  updateVLayerFeatures,
} from './utils';

import 'ol/ol.css';
import './style.css';

const OSM = ({
  olShapes,
  mapProvider,
  tooltips,
}) => {
  const popupRef = useRef(null);

  const [map, setMap] = useState({});
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipComponent, setTooltipComponent] = useState(<></>);

  useEffect(() => {
    // const gmaps = new GoogleLayer({
    //   visible: mapProvider === 'gmaps',
    //   name: 'gmaps',
    // });

    const osm = new TileLayer({
      source: new OSMSource(),
      visible: mapProvider === 'osm',
      name: 'osm',
    });

    const routes = new VectorLayer({
      source: new VectorSource({
        features: olShapes,
      }),
      name: 'vector-layer',
    });

    const layers = [
      // gmaps,
      osm,
      routes,
    ];

    // Create map object with feature layer
    const olMap = new OLMap({
      layers,
      target: 'map', // id attribute of DOM element
      view: new View({
        center: latLonToMercator([ 0, 0 ]),
        zoom: 17,
      }),
    });

    olMap.on('click', (e) => {
      const feature = extractFeatureWithTooltip(olMap, e, tooltips);

      const overlayContainer = document.querySelector('.ol-overlay-container.ol-selectable');
      removeOverlayElementIfAny(overlayContainer);
      
      if (feature) {
        setShowTooltip(true);
        const TooltipComponent = tooltips[feature.get('name')]
        setTooltipComponent(<TooltipComponent olFeature={feature} />);

        const tooltip = setupTooltip(popupRef.current, e);

        olMap.addOverlay(tooltip);
      }
    });

    setMap(olMap);

    // Activate Google layer
    // const OLGMaps = new OLGoogleMaps({
    //   map: olMap,
    //   watch: {
    //     image: true,
    //     tile: true,
    //     vector: true,
    //   },
    // });
    // OLGMaps.activate();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const overlayContainer = document.querySelector('.ol-overlay-container.ol-selectable');
    removeOverlayElementIfAny(overlayContainer);

    if (Object.keys(map || {}).length) {
      const vLayer = findVectorLayer(map, 'vector-layer');

      if (vLayer) {
        updateVLayerFeatures(vLayer, olShapes);
        fitMap(map, vLayer);
      }
    }
  }, [ map, olShapes ]);

  return (
    <div>
      <div id="map" />
      <div className="popup" ref={popupRef}>
        {showTooltip && tooltipComponent && tooltipComponent}
      </div>
    </div>
  );
};

export default OSM;
