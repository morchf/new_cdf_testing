CREATE TABLE IF NOT EXISTS gtfs.routes (
  route_id TEXT ENCODE raw,
  agency_id TEXT ENCODE raw,
  route_short_name TEXT ENCODE raw,
  route_long_name TEXT ENCODE raw,
  route_desc TEXT ENCODE raw,
  route_type bigint ENCODE raw,
  route_url TEXT ENCODE raw,
  route_color TEXT ENCODE raw,
  route_text_color TEXT ENCODE raw,
  route_sort_order bigint ENCODE raw,
  continuous_pickup bigint ENCODE raw,
  continuous_drop_off bigint ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)