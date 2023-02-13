/*
Segment-based calculations to distinctly identify intersection events for drive segments
*/
CREATE TABLE IF NOT EXISTS public.intersection_events (
  agency_id TEXT,
  trip_instance_id TEXT,

  /*
  VehiclePosition
  */
  "timestamp" TIMESTAMP,
  intersection_id TEXT, -- ID of closest intersection (within 30 meters)
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  speed DOUBLE PRECISION,

  -- TripDescriptor
  trip_id TEXT,
  route_id CHARACTER VARYING(512),
  trip_direction_id TEXT,
  trip_start_time TIMESTAMP,
  trip_start_date TEXT,

  /*
  Additional
  */
  -- Segment-based metrics
  segment INT,              -- Segment number
  duration DOUBLE PRECISION, -- Duration of trip attributed to event

  -- Meta
  source_device TEXT -- RT_GTFS, CVP, 2101-TSP
);
