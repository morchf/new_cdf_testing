import React, { useCallback, useMemo, useRef } from 'react';
import { GoogleMap, InfoWindow, useLoadScript } from '@react-google-maps/api';
import { GMAPS_KEY } from '../../../constants';
import { fitGMap } from './utils';

import './style.css';

// References for marker types
// https://developers.google.com/maps/documentation/javascript/reference/map?hl=en#MapTypeStyle
// https://developers.google.com/maps/documentation/javascript/style-reference#style-features
// https://developers.google.com/maps/documentation/javascript/style-reference#style-elements

const mapStyles = [
  {
    featureType: 'water',
    elementType: 'geometry',
    stylers: [
      {
        color: '#e9e9e9',
      },
      {
        lightness: 17,
      },
    ],
  },
  {
    featureType: 'landscape',
    elementType: 'geometry',
    stylers: [
      {
        color: '#f5f5f5',
      },
      {
        lightness: 20,
      },
    ],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry.fill',
    stylers: [
      {
        color: '#ffffff',
      },
      {
        lightness: 17,
      },
    ],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry.stroke',
    stylers: [
      {
        color: '#ffffff',
      },
      {
        lightness: 29,
      },
      {
        weight: 0.2,
      },
    ],
  },
  {
    featureType: 'road.arterial',
    elementType: 'geometry',
    stylers: [
      {
        color: '#ffffff',
      },
      {
        lightness: 18,
      },
    ],
  },
  {
    featureType: 'road.local',
    elementType: 'geometry',
    stylers: [
      {
        color: '#ffffff',
      },
      {
        lightness: 16,
      },
    ],
  },
  {
    featureType: 'poi',
    elementType: 'geometry',
    stylers: [
      {
        color: '#f5f5f5',
      },
      {
        lightness: 21,
      },
    ],
  },
  {
    featureType: 'poi.park',
    elementType: 'geometry',
    stylers: [
      {
        color: '#dedede',
      },
      {
        lightness: 21,
      },
    ],
  },
  {
    elementType: 'labels.text.stroke',
    stylers: [
      {
        visibility: 'on',
      },
      {
        color: '#ffffff',
      },
      {
        lightness: 16,
      },
    ],
  },
  {
    elementType: 'labels.text.fill',
    stylers: [
      {
        saturation: 36,
      },
      {
        color: '#333333',
      },
      {
        lightness: 40,
      },
    ],
  },
  {
    elementType: 'labels.icon',
    stylers: [
      {
        visibility: 'off',
      },
    ],
  },
  {
    featureType: 'transit',
    elementType: 'geometry',
    stylers: [
      {
        color: '#f2f2f2',
      },
      {
        lightness: 19,
      },
    ],
  },
  {
    featureType: 'administrative',
    elementType: 'geometry.fill',
    stylers: [
      {
        color: '#fefefe',
      },
      {
        lightness: 20,
      },
    ],
  },
  {
    featureType: 'administrative',
    elementType: 'geometry.stroke',
    stylers: [
      {
        color: '#fefefe',
      },
      {
        lightness: 17,
      },
      {
        weight: 1.2,
      },
    ],
  },
];

const GMaps = ({
  gmapsShapes = [],
  selectedMapItemState = [null, () => {}],
  tooltips = {},
  onViewportBoundsChanged = () => {},
  children,
}) => {
  const locations = useMemo(
    () =>
      gmapsShapes.reduce((accumulator, shapeComponent) => {
        if (shapeComponent.props.position) {
          return [...accumulator, shapeComponent.props.position];
        }

        if (shapeComponent.props.path) {
          return [...accumulator, ...shapeComponent.props.path];
        }

        return accumulator;
      }, []),
    [gmapsShapes]
  );

  const [selectedMarker, setSelectedMarker] = selectedMapItemState;
  const mapRef = useRef();
  const mapContainer = useRef();

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: GMAPS_KEY,
  });

  const onMapLoad = useCallback(
    (map) => {
      mapRef.current = map;
      const width = mapContainer?.current?.offsetWidth;
      const height = mapContainer?.current?.offsetHeight;

      fitGMap(locations, map, { width, height });
    },
    [locations]
  );

  if (loadError) return 'Error';
  if (!isLoaded) return 'Loading...';

  return (
    <div className="google-maps-container" ref={mapContainer}>
      <GoogleMap
        id="map"
        options={{
          styles: mapStyles,
          disableDefaultUI: true,
          zoomControl: true,
          zoomControlOptions: {
            position: 6,
          },
        }}
        onLoad={onMapLoad}
        onIdle={() => {
          if (!mapRef?.current?.getBounds()) return;

          const ne = mapRef.current.getBounds().getNorthEast();
          const sw = mapRef.current.getBounds().getSouthWest();

          onViewportBoundsChanged({
            ne: { lat: ne.lat(), lon: ne.lng() },
            sw: { lat: sw.lat(), lon: +sw.lng() },
          });
        }}
      >
        {children}
        {gmapsShapes}
        {selectedMarker ? (
          <InfoWindow
            position={{
              lat: parseFloat(selectedMarker?.lat),
              lng: parseFloat(selectedMarker?.lon),
            }}
            onCloseClick={() => setSelectedMarker(null)}
          >
            <div style={{ width: 'max-content' }}>
              {tooltips.marker(selectedMarker)}
            </div>
          </InfoWindow>
        ) : null}
      </GoogleMap>
    </div>
  );
};

export default GMaps;
