CREATE TABLE IF NOT EXISTS gtfs.shapes (
  shape_id TEXT ENCODE raw,
  shape_pt_lat double precision ENCODE raw,
  shape_pt_lon double precision ENCODE raw,
  shape_pt_sequence bigint ENCODE raw,
  shape_dist_traveled double precision ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)