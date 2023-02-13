CREATE TABLE IF NOT EXISTS gtfs.stop_times (
  trip_id TEXT ENCODE raw,
  arrival_time TEXT ENCODE raw,
  departure_time TEXT ENCODE raw,
  stop_id TEXT ENCODE raw,
  stop_sequence bigint ENCODE raw,
  stop_headsign TEXT ENCODE raw,
  pickup_type bigint ENCODE raw,
  drop_off_type bigint ENCODE raw,
  continuous_pickup bigint ENCODE raw,
  continuous_drop_off bigint ENCODE raw,
  shape_dist_traveled double precision ENCODE raw,
  timepoint bigint ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)