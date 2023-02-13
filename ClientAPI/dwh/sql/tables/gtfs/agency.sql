CREATE TABLE IF NOT EXISTS gtfs.agency (
  agency_id TEXT ENCODE raw,
  agency_name TEXT ENCODE raw,
  agency_url TEXT ENCODE raw,
  agency_timezone TEXT ENCODE raw,
  agency_lang TEXT ENCODE raw,
  agency_phone TEXT ENCODE raw,
  agency_fare_url TEXT ENCODE raw,
  agency_email TEXT ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)