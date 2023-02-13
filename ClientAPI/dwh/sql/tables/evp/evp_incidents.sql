CREATE TABLE IF NOT EXISTS evp.evp_incidents (
  event_number TEXT,
  dispatch_number TEXT,
  unit TEXT,
  dispatched TIMESTAMP,
  enroute TIMESTAMP,
  arrival TIMESTAMP,
  enroute_to_hospital TIMESTAMP,
  hospital_arrival TIMESTAMP,
  clear_time TIMESTAMP,
  "location" TEXT,
  municipality TEXT,
  latitude TEXT,
  longitude TEXT,
  agency_id TEXT,
  "date" DATE,
  load_utc_date TEXT
)
