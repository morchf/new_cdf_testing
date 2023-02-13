INSERT INTO evp.evp_incidents
SELECT event_number,
  dispatch_number,
  unit,
  TO_TIMESTAMP(dispatched, 'MM/DD/YY HH24:MI:SS') AS dispatched,
  CASE
    WHEN enroute = 'NULL' THEN NULL
    ELSE TO_TIMESTAMP(enroute, 'MM/DD/YY HH24:MI:SS')
  END AS enroute,
  CASE
    WHEN arrival = 'NULL' THEN NULL
    ELSE TO_TIMESTAMP(arrival, 'MM/DD/YY HH24:MI:SS')
  END AS arrival,
  CASE
    WHEN enroute_to_hospital = 'NULL' THEN NULL
    ELSE TO_TIMESTAMP(enroute_to_hospital, 'MM/DD/YY HH24:MI:SS')
  END AS enroute_to_hospital,
  CASE
    WHEN hospital_arrival = 'NULL' THEN NULL
    ELSE TO_TIMESTAMP(hospital_arrival, 'MM/DD/YY HH24:MI:SS')
  END AS hospital_arrival,
  CASE
    WHEN clear_time = 'NULL' THEN NULL
    ELSE TO_TIMESTAMP(clear_time, 'MM/DD/YY HH24:MI:SS')
  END AS clear_time,
  "location",
  municipality,
  latitude,
  longitude,
  agency_id,
  (
    TO_TIMESTAMP(dispatched, 'MM/DD/YY HH24:MI:SS')
  )::DATE AS "date",
  utc_date AS load_date
FROM ext_evp.incidents AS i (
    event_number,
    dispatch_number,
    unit,
    dispatched,
    enroute,
    arrival,
    enroute_to_hospital,
    hospital_arrival,
    clear_time,
    "location",
    municipality,
    latitude,
    longitude
  )
WHERE LEN(dispatched) <= 15