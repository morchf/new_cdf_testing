import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  GoogleMap,
  useLoadScript,
  Marker,
  OverlayView,
} from '@react-google-maps/api';
import Skeleton from '../../../../common/components/Skeleton';
import ApproachesModal from '../ApproachesModal';
import mapStyles from './mapStyles';
import './style.css';

// Required libraries for drawing on map and using certain computation methods
const libraries = ['drawing', 'geometry'];

const approachStyle = {
  90: {
    label: 'NB',
    approachName: 'Northbound',
    extendedLabel: 'Nourthbound Approach',
    color: 'purple',
  },
  180: {
    label: 'EB',
    approachName: 'Eastbound',
    extendedLabel: 'Eastbound Approach',
    color: 'orange',
  },
  270: {
    label: 'SB',
    approachName: 'Southbound',
    extendedLabel: 'Southbound Approach',
    color: 'green',
  },
  360: {
    label: 'WB',
    approachName: 'Westbound',
    extendedLabel: 'Westbound Approach',
    color: 'yellow',
  },
};

const lineSymbol = {
  path: 'M 0,-1 0,1',
  strokeOpacity: 1,
  strokeWeight: 1,
  scale: 1,
};

const polygonOptions = {
  strokeOpacity: 0,
  strokeWeight: 0,
  fillOpacity: 0.6,
};

const polylineOptions = {
  strokeOpacity: 0,
  icons: [
    {
      icon: lineSymbol,
      offset: '0%',
      repeat: '5px',
    },
  ],
};

const computeDirection = (startPoint, endPoint) => {
  const heading = window.google.maps.geometry.spherical.computeHeading(
    startPoint,
    endPoint
  );

  // Headings are computer relative to global North (represented as 0 degrees)
  // Headings are in range -180 to 180 degrees
  // Computing offsets later on requires degrees ranging from 0 to 360, so we
  // need to convert
  let direction = heading;
  if (heading < -90 && heading >= -180) direction += 450;
  else direction += 90;
  return direction;
};

const ApproachesMap = ({
  isLoading,
  lat,
  lng,
  approachMap,
  generalData,
  onApproachMapChange,
}) => {
  const [approaches, setApproaches] = useState([]);
  const [drawingManager, setDrawingManager] = useState(undefined);
  const [approachesArr, setApproachesArr] = useState([]);
  const [polylinesArr, setPolylinesArr] = useState([]);
  const [labels, setLabels] = useState([]);
  const mapRef = useRef();

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GMAPS_KEY,
    libraries,
  });

  const drawMap = useCallback(
    (userPoints) => {
      if (isLoading || !isLoaded) return null;

      const approachData = {};
      approachData.numberOfCoordinates = userPoints.length;

      // Get methods for computing distances, headings, etc.
      // Grab endpoints from user-drawn line
      const { maps } = window.google;
      const approachLength =
        Math.round(maps.geometry.spherical.computeLength(userPoints) * 100) /
        100;
      const nearestPoints = userPoints.slice(0, 2);

      const point0Distance =
        Math.round(
          maps.geometry.spherical.computeLength([
            {
              lat,
              lng,
            },
            {
              lat: nearestPoints[0].lat(),
              lng: nearestPoints[0].lng(),
            },
          ]) * 100
        ) / 100;
      const point1Distance =
        Math.round(
          maps.geometry.spherical.computeLength([
            {
              lat,
              lng,
            },
            {
              lat: nearestPoints[1].lat(),
              lng: nearestPoints[1].lng(),
            },
          ]) * 100
        ) / 100;
      const finalSegmentDirection =
        lat && lng
          ? point0Distance < point1Distance
            ? computeDirection(nearestPoints[0], nearestPoints[1])
            : computeDirection(nearestPoints[1], nearestPoints[0])
          : computeDirection(nearestPoints[0], nearestPoints[1]);
      let cardinalDirection = 90;
      if (finalSegmentDirection >= 135 && finalSegmentDirection < 225)
        cardinalDirection = 180;
      if (finalSegmentDirection >= 225 && finalSegmentDirection < 315)
        cardinalDirection = 270;
      if (
        (finalSegmentDirection >= 315 && finalSegmentDirection <= 360) ||
        (finalSegmentDirection >= 0 && finalSegmentDirection <= 45)
      )
        cardinalDirection = 360;
      const { label, approachName, extendedLabel, color } =
        approachStyle[cardinalDirection];

      approachData.approachName = approachName;
      approachData.coordinates = [];

      // Remove existing polylines and labels
      setApproachesArr((a) => {
        a.filter(
          ({ cardinalDirection: cd }) => cd === cardinalDirection
        ).forEach((pl) => pl.setMap(null));

        return a.filter(
          ({ cardinalDirection: cd }) => cd !== cardinalDirection
        );
      });
      setPolylinesArr((p) => {
        p.filter(
          ({ cardinalDirection: cd }) => cd === cardinalDirection
        ).forEach((pl) => pl.setMap(null));

        return p.filter(
          ({ cardinalDirection: cd }) => cd !== cardinalDirection
        );
      });
      setLabels((l) =>
        l.filter(
          ({ props: { cardinalDirection: cd } }) => cd !== cardinalDirection
        )
      );
      // For every line segment drawn by the user, create an approach segment
      for (let i = 0; i < userPoints.length - 1; i++) {
        const startPoint = userPoints[i];
        const endPoint = userPoints[i + 1];
        const radius = 30;

        approachData.coordinates[i] = {
          latitude: startPoint.lat().toFixed(6),
          longitude: startPoint.lng().toFixed(6),
          width: radius,
        };
        approachData.coordinates[i + 1] = {
          latitude: endPoint.lat().toFixed(6),
          longitude: endPoint.lng().toFixed(6),
          width: radius,
        };

        const length =
          Math.round(
            maps.geometry.spherical.computeDistanceBetween(
              startPoint,
              endPoint
            ) * 100
          ) / 100;

        const direction = computeDirection(startPoint, endPoint);

        const directionEast = direction - 180;
        const directionWest = direction;

        const pointOne = maps.geometry.spherical.computeOffset(
          startPoint,
          radius,
          directionEast
        );
        const pointTwo = maps.geometry.spherical.computeOffset(
          startPoint,
          radius,
          directionWest
        );
        const pointThree = maps.geometry.spherical.computeOffset(
          endPoint,
          radius,
          directionWest
        );
        const pointFour = maps.geometry.spherical.computeOffset(
          endPoint,
          radius,
          directionEast
        );

        const approachCoords = [
          { lat: pointOne.lat(), lng: pointOne.lng() },
          { lat: pointTwo.lat(), lng: pointTwo.lng() },
          { lat: pointThree.lat(), lng: pointThree.lng() },
          { lat: pointFour.lat(), lng: pointFour.lng() },
        ];

        // Add polygon with the filled in color, but no border
        const approach = new maps.Polygon({
          path: approachCoords,
          options: {
            ...polygonOptions,
            fillColor: color,
          },
          map: mapRef.current,
        });
        approach.cardinalDirection = cardinalDirection;

        setApproachesArr((a) => [...a, approach]);
        // Add polyline to create a border on top of the polygon
        const polyline = new maps.Polyline({
          path: approachCoords,
          options: polylineOptions,
          map: mapRef.current,
        });
        polyline.cardinalDirection = cardinalDirection;

        setPolylinesArr((p) => [...p, polyline]);

        // Calculating the center of the polygon so we can add other elements to it
        const approachBounds = new maps.LatLngBounds();

        for (let x = 0; x < approachCoords.length; x++) {
          approachBounds.extend(approachCoords[x]);
        }

        // Add labels to each approach, based off of the current style
        setLabels((l) => {
          const labelEl = (
            <OverlayView
              key={`${l.length}-${cardinalDirection}`}
              position={{
                lat: approachBounds.getCenter().lat(),
                lng: approachBounds.getCenter().lng(),
              }}
              mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
              getPixelPositionOffset={(width, height) => ({
                x: -(width / 2),
                y: -(height / 4),
              })}
              // Keep track of label type
              cardinalDirection={cardinalDirection}
            >
              <p
                style={{
                  fontSize: '12.5px',
                  transform: `rotate(${direction - 90}deg)`,
                }}
              >
                <b>{label}</b>
              </p>
            </OverlayView>
          );

          return [...l, labelEl];
        });

        // Here InfoWindow gets added to the newly created polygon
        // to display info about segment and approach length/distance
        // to intersection
        approach.infoWindow = new maps.InfoWindow({
          content: `
          <div style="width:225px;">
              <h3>${extendedLabel}</h3>
              <p>Segment Length: ${+length}m</p>
              <p>Total Distance to Intersection: ${+approachLength}m</p>
          </div>
        `,
          position: {
            lat: approachBounds.getCenter().lat(),
            lng: approachBounds.getCenter().lng(),
          },
        });

        // eslint-disable-next-line func-names
        maps.event.addListener(approach, 'click', function () {
          // eslint-disable-next-line no-invalid-this
          this.infoWindow.open(mapRef.current, this);
        });
      }

      return approachData;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lat, lng, isLoading, isLoaded, mapRef?.current]
  );

  useEffect(() => {
    if (isLoading || !isLoaded) return;
    if (!(approachMap && window.google)) return;
    const { maps } = window.google;

    approachMap.forEach((data, index) => {
      const userPoints = [];

      const approachCoordinates = data.coordinates;
      approachCoordinates.forEach((d) => {
        const boundedLat =
          Math.sign(d.latitude) *
          Math.min(d.latitude * Math.sign(d.latitude), 90);
        const boundedLng =
          Math.sign(d.longitude) *
          Math.min(d.longitude * Math.sign(d.longitude), 180);

        userPoints.push(new maps.LatLng(boundedLat, boundedLng));
      });
      drawMap(userPoints);
    });

    setApproaches(approachMap);
  }, [approachMap, drawMap, isLoaded, isLoading]);

  const onPolylineComplete = useCallback(
    (polyline) => {
      const userPoints = polyline.getPath().getArray();
      const newApproachMap = drawMap(userPoints);
      onApproachMapChange((am) => [
        ...am.filter(
          ({ approachName: an }) => an !== newApproachMap.approachName
        ),
        newApproachMap,
      ]);
      // Remove original user polyline from map
      polyline.setMap(null);
    },
    [drawMap, onApproachMapChange]
  );

  const mapOptions = {
    styles: mapStyles,
    disableDefaultUI: true,
    zoomControl: false,
    scrollwheel: false,
    disableDoubleClickZoom: true,
  };

  const center = {
    lat: parseFloat(lat),
    lng: parseFloat(lng),
  };

  const onMapLoad = useCallback(
    (map) => {
      mapRef.current = map;
      const dm = new window.google.maps.drawing.DrawingManager({
        drawingControl: false,
      });
      dm.setMap(map);

      window.google.maps.event.addListener(
        dm,
        'polylinecomplete',
        onPolylineComplete
      );
      setDrawingManager(dm);
    },
    [onPolylineComplete]
  );

  return (
    <div>
      {!isLoading && isLoaded ? (
        <GoogleMap
          id="map"
          zoom={15}
          center={center}
          options={mapOptions}
          onLoad={onMapLoad}
        >
          <Marker
            icon={{
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 5,
            }}
            position={center}
          />
          <ApproachesModal
            drawingManager={drawingManager}
            generalData={generalData}
          />
          {labels}
        </GoogleMap>
      ) : (
        <Skeleton number={1} className="map__skeleton" active={isLoading} />
      )}
    </div>
  );
};

export default ApproachesMap;
