// import React from 'react';
import { Marker, Polyline } from '@react-google-maps/api';

export const getMarker = (
  marker = {},
  handleClick = () => {},
  icon = {},
  key = 'marker',
  label = ''
) => {
  const isIconFunction = typeof icon === 'function';

  let { lat, lon: lng } = marker;
  lat = parseFloat(lat);
  lng = parseFloat(lng);

  const onClick = () => handleClick(marker);

  return (
    <Marker
      key={`marker-${key}-${lat}-${lng}`}
      position={{ lat, lng }}
      onClick={onClick}
      icon={isIconFunction ? icon(marker) : icon}
      label={label}
    />
  );
};

export const getPolyline = (
  segment,
  options = {},
  key = 'polyline',
  handleClick = () => {}
) => {
  const optionsIsFunction = typeof options === 'function';

  const path = segment?.points?.map(({ lat, lon }) => ({
    lat: parseFloat(lat),
    lng: parseFloat(lon),
  }));

  const onClick = () => handleClick(segment);

  return (
    <Polyline
      key={`polyline-${key}`}
      path={path}
      onClick={onClick}
      options={optionsIsFunction ? options(segment?.points) : options}
    />
  );
};
