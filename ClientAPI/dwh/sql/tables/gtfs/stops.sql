CREATE TABLE IF NOT EXISTS gtfs.stops (
  stop_id TEXT ENCODE raw,
  stop_code TEXT ENCODE raw,
  stop_name TEXT ENCODE raw,
  tts_stop_name TEXT ENCODE raw,
  stop_desc TEXT ENCODE raw,
  stop_lat double precision ENCODE raw,
  stop_lon double precision ENCODE raw,
  zone_id TEXT ENCODE raw,
  stop_url TEXT ENCODE raw,
  location_type bigint ENCODE raw,
  parent_station TEXT ENCODE raw,
  stop_timezone TEXT ENCODE raw,
  wheelchair_boarding bigint ENCODE raw,
  level_id TEXT ENCODE raw,
  platform_code TEXT ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)