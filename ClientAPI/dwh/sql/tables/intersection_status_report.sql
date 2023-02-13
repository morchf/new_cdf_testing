CREATE TABLE IF NOT EXISTS public.intersection_status_report (
  deviceid TEXT ENCODE raw,
  locationid TEXT ENCODE raw,
  locationname TEXT ENCODE raw,
  device TEXT ENCODE raw,
  applicationfirmwareversion TEXT ENCODE raw,
  lastlogretrieved TEXT ENCODE raw,
  latitude TEXT ENCODE raw,
  longitude TEXT ENCODE raw,
  cha TEXT ENCODE raw,
  chb TEXT ENCODE raw,
  chc TEXT ENCODE raw,
  chd TEXT ENCODE raw,
  status TEXT ENCODE raw,
  details CHARACTER VARYING(1024) ENCODE raw,
  date_ran date ENCODE raw,
  agency TEXT ENCODE raw,
  date TEXT ENCODE raw
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date)