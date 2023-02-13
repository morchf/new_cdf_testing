/*
Segment-based calculations to distinctly identify stop events for drive segments
*/
CREATE TABLE IF NOT EXISTS public.segment_events (
  agency_id TEXT,
  trip_instance_id TEXT,

  /*
  VehiclePosition
  */
  "timestamp" TIMESTAMP,
  stop_id TEXT,
  current_status TEXT,       -- STOPPED_AT, NEAR_STOP, IN_TRANSIT_TO
  current_stop_sequence INT, -- (Optional)
  congestion_level TEXT,     -- (Optional) UNKNOWN_CONGESTION_LEVEL, RUNNING_SMOOTHLY, STOP_AND_GO, CONGESTION, SEVERE_CONGESTION
  occupancy_status TEXT,     -- (Optional) EMPTY, MANY_SEATS_AVAILABLE, FEW_SEATS_AVAILABLE, STANDING_ROOM_ONLY, CRUSHED_STANDING_ROOM_ONLY, FULL, NOT_ACCEPTING_PASSENGERS

  -- VehicleDescriptor
  vehicle_id TEXT,    -- (Optional)
  vehicle_label TEXT, -- (Optional)
  license_plate TEXT, -- (Optional)

  -- Position
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  speed DOUBLE PRECISION,
  odometer DOUBLE PRECISION,
  bearing DOUBLE PRECISION,

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
  segment INT,              -- Segment number (stop-to-stop)
  stop_start_id TEXT,       -- Segment stop start
  stop_end_id TEXT,         -- Segment stop end
  duration DOUBLE PRECISION, -- Duration of trip attributed to event
 
  -- Meta
  source_device TEXT -- RT_GTFS, CVP, 2101-TSP
);
