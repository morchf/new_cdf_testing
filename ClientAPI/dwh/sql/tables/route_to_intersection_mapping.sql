CREATE TABLE IF NOT EXISTS public.route_to_intersection_mapping (
  route_id TEXT ENCODE raw,
  route_short_name TEXT ENCODE raw,
  direction_id bigint ENCODE raw,
  deviceid TEXT ENCODE raw,
  latitude TEXT ENCODE raw,
  longitude TEXT ENCODE raw,
  sequence bigint ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)