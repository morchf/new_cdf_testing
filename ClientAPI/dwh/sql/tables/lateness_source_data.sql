CREATE TABLE IF NOT EXISTS public.lateness_source_data (
  route TEXT,
  direction TEXT,
  stopstart TEXT,
  stopstarttime TIMESTAMP,
  stopstartlateness INT,
  stopstartlatitude DOUBLE PRECISION,
  stopstartlongitude DOUBLE PRECISION,
  stopend TEXT,
  stopendtime TIMESTAMP,
  stopendlateness INT,
  stopendlatitude DOUBLE PRECISION,
  stopendlongitude DOUBLE PRECISION,
  numintersections BIGINT,
  vehiclepassthrough INT,
  numrequests BIGINT,
  latenessreduction INT,
  gtt_trip_id TEXT,
  stopstartid TEXT,
  stopendid TEXT,
  agency TEXT,
  "date" TEXT
) DISTSTYLE EVEN COMPOUND SORTKEY (agency, date);

