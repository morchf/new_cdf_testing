/*
Segment-based calculations to distinctly identify intersection events for drive segments
*/
CREATE TABLE IF NOT EXISTS evp_events (
  agency_id TEXT,
  trip_instance_id TEXT,

  "timestamp" TIMESTAMP,
  intersection_id TEXT, -- ID of closest intersection (within 30 meters)
  current_status TEXT,       -- AT_INTERSCTION, IN_TRANSIT_TO
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  speed DOUBLE PRECISION,

  trip_start_time TIMESTAMP,
  trip_start_date TEXT,

  -- Segment-based metrics
  segment INT,                -- Segment number
  intersection_start_id TEXT, -- Segment intersection start
  intersection_end_id TEXT,   -- Segment intersection end
  duration DOUBLE PRECISION   -- Duration of trip attributed to event
) DISTSTYLE EVEN;
