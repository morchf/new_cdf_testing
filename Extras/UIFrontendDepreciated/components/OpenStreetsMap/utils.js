import Overlay from 'ol/Overlay';

export const fitMap = (map, vectorLayer) => {
  const vectorSource = vectorLayer.getSource();

  if (vectorLayer.getSource().getFeatures().length > 0) {
    map.getView().fit(vectorSource.getExtent(), map.getSize());
  }
};

export const extractFeatureWithTooltip = (map, e, tooltips) => {
  // eslint-disable-next-line consistent-return
  const feature = map.forEachFeatureAtPixel(e.pixel, (olFeature) => {
    const featureHasTooltip = Object.keys(tooltips || {}).includes(olFeature.get('name'));
    if (featureHasTooltip) return olFeature;
  });

  return feature;
};

export const setupTooltip = (element, e) => {
  const tooltip = new Overlay({
    element,
    offset: [0, -15],
    positioning: 'bottom-center',
    stopEvent: false,
    insertFirst: false,
  });

  tooltip.setPosition(e.coordinate);

  return tooltip;
};

export const removeOverlayElementIfAny = (overlayContainer) => {
  if (overlayContainer) {
    overlayContainer.parentNode.removeChild(overlayContainer);
  }
};

export const findVectorLayer = (map, neededLayerName) => {
  const mapLayers = map?.getLayers()?.getArray();
  const vLayer = mapLayers?.filter(layer => {
    const layerName = layer?.get('name');
    return layerName === neededLayerName;
  })[0];

  return vLayer;
};

export const updateVLayerFeatures = (vLayer, newFeatures) => {
  const vectorSource = vLayer.getSource();
  const features = vectorSource.getFeatures();

  if (features) features?.forEach(feature => {
    vectorSource.removeFeature(feature);
  });

  if (Array.isArray(newFeatures)) newFeatures?.forEach(feature => {
    vectorSource.addFeature(feature);
  });
};
