CREATE TABLE IF NOT EXISTS gtfs.trips (
  route_id TEXT ENCODE raw,
  service_id TEXT ENCODE raw,
  trip_id TEXT ENCODE raw,
  trip_headsign TEXT ENCODE raw,
  trip_short_name TEXT ENCODE raw,
  direction_id bigint ENCODE raw,
  block_id TEXT ENCODE raw,
  shape_id TEXT ENCODE raw,
  wheelchair_accessible bigint ENCODE raw,
  bikes_allowed bigint ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)