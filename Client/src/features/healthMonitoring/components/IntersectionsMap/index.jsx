import React, { useState, useRef, useCallback } from 'react';
import {
  GoogleMap,
  useLoadScript,
  Marker,
  InfoWindow,
} from '@react-google-maps/api';
import mapStyles from './mapStyles';
import {
  COLOR_ERROR,
  COLOR_NORMAL,
  COLOR_WARNING,
} from '../../../../common/constants';

const options = {
  styles: mapStyles,
  disableDefaultUI: true,
  zoomControl: true,
  zoomControlOptions: {
    position: 6,
  },
};

// TODO: automated the center calculation
const center = {
  lat: 37.7673332,
  lng: -122.43867471,
};
export default function IntersectionsMap({
  intersections,
  selectedIntersections,
}) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GMAPS_KEY,
  });
  const [selected, setSelected] = useState(null);

  const mapRef = useRef();
  const onMapLoad = useCallback((map) => {
    mapRef.current = map;
  }, []);

  if (loadError) return 'Error';
  if (!isLoaded) return 'Loading...';

  const markers =
    selectedIntersections.length === 0
      ? intersections
      : intersections.filter((intersection) =>
          selectedIntersections.includes(intersection.locationname)
        );

  return (
    <div className="intersections-map-container">
      <GoogleMap
        id="map"
        zoom={13}
        center={center}
        options={options}
        onLoad={onMapLoad}
      >
        {markers !== []
          ? markers.map((marker) => {
              let fillColor;
              if (marker.status === 'Normal') {
                fillColor = COLOR_NORMAL;
              } else if (marker.status === 'Error') {
                fillColor = COLOR_ERROR;
              } else {
                fillColor = COLOR_WARNING;
              }

              return (
                <Marker
                  key={`${marker.latitude}-${marker.longitude}`}
                  position={{ lat: marker.latitude, lng: marker.longitude }}
                  onClick={() => {
                    setSelected(marker);
                  }}
                  icon={{
                    path: 'M10,3c-3.866,0-7,3.133-7,7c0,3.865,3.134,7,7,7s7-3.135,7-7C17,6.133,13.866,3,10,3z',
                    fillColor,
                    fillOpacity: 1,
                    strokeWeight: 0,
                    scale: 0.6,
                  }}
                />
              );
            })
          : null}

        {selected && (
          <InfoWindow
            position={{ lat: selected.latitude, lng: selected.longitude }}
            onCloseClick={() => {
              setSelected(null);
            }}
          >
            <div style={{ width: 'max-content' }}>{selected.locationname}</div>
          </InfoWindow>
        )}
      </GoogleMap>
    </div>
  );
}
