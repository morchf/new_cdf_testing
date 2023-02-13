CREATE TABLE IF NOT EXISTS assets.intersections (
  route_id TEXT,
  "route" TEXT,
  trip_direction_id INT,
  device_id TEXT,
  location_id TEXT,
  street_address TEXT,
  latitude FLOAT,
  longitude FLOAT,
  "sequence" INT,
  agency TEXT,
  agency_id TEXT,
  utc_date TEXT
)
